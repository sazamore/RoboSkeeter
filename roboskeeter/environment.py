__author__ = 'richard'

import numpy as np
import pandas as pd
from scipy.interpolate import Rbf
from scipy.spatial import cKDTree as kdt

from roboskeeter.io.i_o import get_directory
from roboskeeter.plotting.plot_environment import plot_windtunnel, plot_plume_gradient, draw_bool_plume


class Environment(object):
    def __init__(self, experiment):
        """
        Generate environmental objects

        Parameters
        ----------
        experiment
            (object)
        """
        self.condition = experiment.experiment_conditions['condition']
        self.bounded = experiment.experiment_conditions['bounded']
        self.plume_model = experiment.experiment_conditions['plume_model'].lower()

        if self.condition == 'Control' and self.plume_model != 'none':
            print "{} plume model selected for control condition, setting instead to no plume.".format(self.plume_model)
            self.plume_model = 'none'

        self.windtunnel = WindTunnel(self.condition)
        self.plume = self._load_plume()
        self.room_temperature = 19.0

    def _load_plume(self):
        if self.plume_model == "boolean":
            plume = BooleanPlume(self)
        elif self.plume_model == "timeavg":
            plume = TimeAvgPlume(self)
        elif self.plume_model == "none":
            plume = NoPlume(self)
        elif self.plume_model == "unaveraged":
            plume = UnaveragedPlume(self)
        else:
            raise NotImplementedError("no such plume type {}".format(self.plume_model))

        return plume


class WindTunnel:
    def __init__(self, experimental_condition):
        """
        experimental_condition

        """
        self.walls = Walls()
        self.boundary = self.walls.boundary
        self.experimental_condition = experimental_condition

        self.heater_l = Heater("Left", self.experimental_condition)
        self.heater_r = Heater("Right", self.experimental_condition)

    def show(self):
        fig, ax = plot_windtunnel(self)
        return fig, ax


class Walls:
    def __init__(self):
        # these are real dims of our wind tunnel
        self.left = -0.127
        self.right = 0.127
        self.upwind = 1.0
        self.downwind = 0.0
        self.ceiling = 0.254
        self.floor = 0.
        self.boundary = [self.downwind, self.upwind, self.left, self.right, self.floor, self.ceiling]

    def check_in_bounds(self, position):
        xpos, ypos, zpos = position
        inside = True
        past_wall = []

        if xpos > self.upwind:  # beyond upwind(upwind) wall (end)
            inside = False
            past_wall.append('upwind')
        if xpos < self.downwind:  # too far behind
            inside = False
            past_wall.append('downwind')
        if ypos < self.left:  # too left
            inside = False
            past_wall.append('left')
        if ypos > self.right:  # too far right
            inside = False
            past_wall.append('right')
        if zpos > self.ceiling:  # too far above
            inside = False
            past_wall.append('ceiling')
        if zpos < self.floor:  # too far below
            inside = False
            past_wall.append('floor')

        return inside, past_wall


class Heater:
    def __init__(self, side, experimental_condition):
        """
        given side, generate heater

        Parameters
        ----------
        side
            {left, right, none, custom coords}
            Location of the heater
        experimental_condition
            determines whether the heater is on or off
        Returns
        -------
        None
        """
        self.side = side
        self.experimental_condition = experimental_condition

        if side == experimental_condition:
            self.is_on = True
            self.color = 'red'
        else:
            self.is_on = False
            self.color = 'black'

        self.zmin, self.zmax, self.diam, self.x_position, self.y_position = self._set_coordinates()

    def _set_coordinates(self):
        x_coord = 0.864
        zmin = 0.03800
        zmax = 0.11340
        diam = 0.00635

        if self.side in "leftLeftLEFT":
            y_coord = -0.0507
        elif self.side in "rightRightRIGHT":
            y_coord = 0.0507
        elif self.side in 'controlControlCONTROL':
            x_coord, y_coord = None, None
        else:
            raise Exception('invalid location type specified')

        return zmin, zmax, diam, x_coord, y_coord


class Plume(object):
    def __init__(self, environment):
        """
        The plume base class
        Parameters
        ----------
        environment
            (object)

        Returns
        -------
        """
        # useful aliases
        self.environment = environment
        self.condition = environment.condition
        self.walls = environment.windtunnel.walls
        self.plume_model = environment.plume_model

        self.left = self.walls.left
        self.right = self.walls.right
        self.upwind = self.walls.upwind
        self.downwind = self.walls.downwind
        self.ceiling = self.walls.ceiling
        self.floor = self.walls.floor
        self.bounds = [self.downwind, self.upwind, self.left, self.right, self.floor, self.ceiling]


class NoPlume(Plume):
    def __init__(self, environment):
        super(self.__class__, self).__init__(environment)

    def check_in_plume_bounds(self, _):
        # always return false
        return False

    def get_nearest_gradient(self, _):
        """if trying to use gradient ascent decision policy with No Plume, return no gradient"""
        return np.array([0., 0., 0.])


class BooleanPlume(Plume):
    """Are you in the plume Y/N"""
    def __init__(self, environment):
        super(self.__class__, self).__init__(environment)

        self.data = self._load_plume_data()

        self.resolution = self._calc_resolution()

    def check_in_plume_bounds(self, position):
        in_windtunnel_bounds, _ = self.walls.check_in_bounds(position)
        x, y, z = position

        x_distances_to_plume_planes = np.abs(self.data['x_position'] - x)

        if x_distances_to_plume_planes.min() > self.resolution:
            # if distance to nearest plume plane is greater than thresh, we are too far upwind or downwind from plume
            # to be inside the plume
            in_plume = False
        elif in_windtunnel_bounds is False:
            # print("WARNING: can't find plumes outside of windtunnel bounds")
            in_plume = False
        else:
            plume_plane = self._get_nearest_plume_plane(x)
            minor_axis = plume_plane.small_radius
            minor_ax_major_ax_ratio = 3
            major_axis = minor_axis * minor_ax_major_ax_ratio

            # check if position is within the elipsoid
            # implementation of http://math.stackexchange.com/a/76463/291217
            value = (((y - plume_plane.y_position) ** 2) / minor_axis ** 2) + \
                    (((z - plume_plane.z_position) ** 2) / major_axis ** 2)

            if value <= 1:
                in_plume = True
            else:
                in_plume = False

        return in_plume

    def show(self):
        fig, ax = plot_windtunnel(self.environment.windtunnel)
        ax.axis('off')
        draw_bool_plume(self, ax=ax)

    def _get_nearest_plume_plane(self, x_position):
        """given x position, find nearest plan"""
        closest_plume_index = (np.abs(self.data['x_position'] - x_position)).argmin()
        plume_plane = self.data.loc[closest_plume_index]

        return plume_plane

    def _load_plume_data(self):
        col_names = ['x_position', 'z_position', 'small_radius']

        if self.condition in 'controlControlCONTROL':
            raise Exception("This block shouldn't ever run.")
        elif self.condition in 'lLleftLeft':
            plume_dir = get_directory('BOOL_LEFT_CSV')
            df = pd.read_csv(plume_dir, names=col_names)
            df['y_position'] = self.environment.windtunnel.heater_l.y_position
        elif self.condition in 'rightRight':
            plume_dir = get_directory('BOOL_RIGHT_CSV')
            df = pd.read_csv(plume_dir, names=col_names)
            df['y_position'] = self.environment.windtunnel.heater_r.y_position
        else:
            raise Exception('problem with loading plume data {}'.format(self.condition))

        return df

    def _calc_resolution(self):
        """ use x data to calculate the resolution"""
        try:
            resolution = abs(self.data.x_position.diff()[1])
        except AttributeError:  # if no plume, can't take diff() of no data
            resolution = None

        return resolution

    def get_nearest_gradient(self, _):
        """if trying to use gradient ascent decision policy with Boolean, return no gradient"""
        return np.array([0., 0., 0.])


class TimeAvgPlume(Plume):
    """time-averaged temperature readings taken inside the windtunnel"""
    # TODO: test TimeAvgPlume
    def __init__(self, environment):
        super(self.__class__, self).__init__(environment)

        # number of x, y, z positions to interpolate the data. numbers chosen to reflect the spacing at which the
        # measurements were taken to avoid gradient values of 0 due to undersampling
        # resolution = (100j, 25j, 25j)  # stored as complex numbers for mgrid to work properly
        interpolation_resolution = .05  # 1 cm

        print "loading raw plume data"
        self._raw_data = self._load_plume_data()
        data_list = self._load_plume_data()

        if len(data_list) == 3:
            print "loading precomputed padded and interpolated data"
            self._raw_data, self.padded_data, self.data = data_list
        elif len(data_list) == 1:
            self._raw_data = data_list[0]
            # print "filling area surrounding measured area with room temperature data"
            # self.padded_data = self._pad_plume_data()
            print "adding sheet of room temp data on outer windtunnel walls"
            self.padded_data = self._room_temp_wall_sheet()
            print "starting interpolation"
            self.data, self.grid_x, self.grid_y, self.grid_z, self.grid_temp = self._interpolate_data(self.padded_data, interpolation_resolution)
            print "calculating gradient"
            self.gradient_x, self.gradient_y, self.gradient_z = self._calc_gradient()

        print "calculating kd-tree"
        self.tree = self._calc_kdtree()

        print """Timeaveraged plume stats:  TODO implement sanity checks
        raw data min temp: {}
        raw data max temp: {}
        interpolated min temp: {}
        interpolated max temp: {}
        """.format(self._raw_data.avg_temp.min(),self._raw_data.avg_temp.max(),
                   self.data.avg_temp.min(), self.data.avg_temp.max())

        print """Warning: we don't know the plume bounds for the Timeavg plume, so the check_for_plume() method
                always returns False"""

    def check_in_plume_bounds(self, *_):
        """
        we don't know the plume bounds for the Timeavg plume, so the check_in_plume_bounds() method
                always returns False

        Returns
        -------
        in_plume
            always return False.
        """

        return False


    def get_nearest_prediction(self, position):
        """
        Given [x,y,z] return nearest temperature data
        Parameters
        ----------
        position
            [x,y,z]

        Returns
        -------
        temperature
        """

        _, index = self.tree.query(position)
        data = self.data.iloc[index]
        return data

    def get_nearest_gradient(self, position):
        data = self.get_nearest_prediction(position)
        return np.array([data['gradient_x'], data['gradient_y'], data['gradient_z']])

    def show_scatter_data(self, selection = 'raw', temp_thresh=0):
        data = self._select_data(selection)
        from roboskeeter.plotting.plot_environment import plot_windtunnel, plot_plume_recordings_scatter
        fig, ax = plot_windtunnel(self.environment.windtunnel)
        plot_plume_recordings_scatter(data, ax, temp_thresh)
        fig.show()

    def show(self):
        import roboskeeter.plotting.plot_environment_mayavi as pemavi
        # fig, ax = plot_windtunnel(self.environment.windtunnel)
        # plot_plume_recordings_scatter(self.data, ax)
        pemavi.plot_plume_recordings_volume(self.bounds, self.grid_x, self.grid_y, self.grid_z, self.grid_temp)
        # fig.show()


    def show_gradient(self):
        import roboskeeter.plotting.plot_environment_mayavi as pemavi
        pemavi.plot_plume_3d_quiver(self.gradient_x, self.gradient_y, self.gradient_z, self.bounds)


    def plot_gradient(self, thresh=0):
        from roboskeeter.plotting.plot_environment import plot_windtunnel, plot_plume_gradient
        fig, ax = plot_windtunnel(self.environment.windtunnel)
        plot_plume_gradient(self, ax, thresh)
        # fig.show()

    def calc_euclidean_distance_neighbords(self, selection='interpolated'):
        data = self._select_data(selection)
        kdtree = self._calc_kdtree(selection)

        coords = data[['x', 'y', 'z']]

        dist_neighbors = np.zeros(len(coords))
        for i in range(len(coords)):
            coord = coords.iloc[i]
            dists, _ = kdtree.query(coord, k=2, p=2)  # euclidean dist, select 2 nearest neighbords
            dist_neighbors[i] = dists[-1]  # select second entry

        return dist_neighbors.mean()

    def _load_plume_data(self):
        """

        Returns
        -------
        list of dataframes

        if precomputed files exist, will return [raw data, padded data, interpolated data]
        else, will return [raw data]
        """
        col_names = ['x', 'y', 'z', 'avg_temp']

        if self.condition in 'controlControlCONTROL':
            return None
        elif self.condition in 'lLleftLeft':
            plume_dir = get_directory('THERMOCOUPLE_TIMEAVG_LEFT_CSV')
            raw = pd.read_csv(plume_dir, names=col_names)
            raw = raw.dropna()

            # check for pre-computed padded files
            try:
                padded_f = get_directory('THERMOCOUPLE_TIMEAVG_LEFT_PADDED_CSV')
                padded_df = pd.read_csv(padded_f)

                interpolated_f = get_directory('THERMOCOUPLE_TIMEAVG_LEFT_INTERPOLATED_CSV')
                interpolated_df = pd.read_csv(interpolated_f)

                return [raw, padded_df, interpolated_df]
            except IOError:  # files doesn't exist
                print "did not find pre-computed padded temps"
                return [raw]

        elif self.condition in 'rightRight':
            plume_dir = get_directory('THERMOCOUPLE_TIMEAVG_RIGHT_CSV')
            raw = pd.read_csv(plume_dir, names=col_names)
            raw = raw.dropna()

            # check for pre-computed padded files
            try:
                padded_f = get_directory('THERMOCOUPLE_TIMEAVG_RIGHT_PADDED_CSV')
                padded_df = pd.read_csv(padded_f)

                interpolated_f = get_directory('THERMOCOUPLE_TIMEAVG_RIGHT_INTERPOLATED_CSV')
                interpolated_df = pd.read_csv(interpolated_f)

                return [raw, padded_df, interpolated_df]
            except IOError:  # files doesn't exist
                print "did not find pre-computed padded temps"
                return [raw]

        else:
            raise Exception('problem with loading plume data {}'.format(self.condition))

    def _room_temp_wall_sheet(self):
        wall_thickness = 0.03  # make sure this value is >= resolution in the _make_uniform_data_grid()
        data_xmin = self.downwind - wall_thickness
        data_xmax = self.upwind + wall_thickness
        data_ymin = self.left - wall_thickness
        data_ymax = self.right + wall_thickness
        data_zmin = self.floor - wall_thickness
        data_zmax = self.ceiling + wall_thickness


        df_list = [self._raw_data]  # start with raw data

        # make a sheet of room temp data for each wall
        df_list.append(self._make_uniform_data_grid(data_xmin, self.downwind, self.left, self.right, self.floor, self.ceiling))
        df_list.append(self._make_uniform_data_grid(self.upwind, data_xmax, self.left, self.right, self.floor, self.ceiling))

        df_list.append(self._make_uniform_data_grid(self.downwind, self.upwind, data_ymin, self.left, self.floor, self.ceiling))
        df_list.append(self._make_uniform_data_grid(self.downwind, self.upwind, self.right, data_ymax, self.floor, self.ceiling))

        df_list.append(self._make_uniform_data_grid(self.downwind, self.upwind, self.left, self.right, data_zmin, self.floor))
        df_list.append(self._make_uniform_data_grid(self.downwind, self.upwind, self.left, self.right, self.ceiling, data_zmax))

        return pd.concat(df_list)

    def _pad_plume_data(self):
        """
        We are assuming that far away from the plume envelope the air will be room temperature. We are padding the
        recorded area with room temperature data points

        Appends the padded data to the raw data
        """

        padding_distance = 0.03  # start padding 3 cm away from recorded data

        data_xmin = self._raw_data.x.min() - padding_distance
        data_xmax = self._raw_data.x.max() + padding_distance
        data_ymin = self._raw_data.y.min() - padding_distance
        data_ymax = self._raw_data.y.max() + padding_distance
        data_zmin = self._raw_data.z.min() - padding_distance
        data_zmax = self._raw_data.z.max() + padding_distance


        df_list = [self._raw_data]  # append to raw data
        # make grids of room temp data to fill the volume surrounding the place we took measurements
        df_list.append(self._make_uniform_data_grid(self.downwind, data_xmin, self.left, self.right, self.floor, self.ceiling))
        df_list.append(self._make_uniform_data_grid(data_xmax, self.upwind, self.left, self.right, self.floor, self.ceiling))

        df_list.append(self._make_uniform_data_grid(data_xmin, data_xmax, self.left, data_ymin, self.floor, self.ceiling))
        df_list.append(self._make_uniform_data_grid(data_xmin, data_xmax, data_ymax, self.right, self.floor, self.ceiling))

        df_list.append(self._make_uniform_data_grid(data_xmin, data_xmax, data_ymin, data_ymax, self.floor, data_zmin))
        df_list.append(self._make_uniform_data_grid(data_xmin, data_xmax, data_ymin, data_ymax, data_zmax, self.ceiling))

        return pd.concat(df_list)

    def _make_uniform_data_grid(self, xmin, xmax, ymin, ymax, zmin, zmax, temp=19., res=0.03):
        # res is resolution in meters
        # left grid
        x = np.arange(xmin, xmax, res)
        y = np.arange(ymin, ymax, res)
        z = np.arange(zmin, zmax, res)
        # we save this grid b/c it helps us with the gradient func
        xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
        df_dict = dict()
        df_dict['x'] = xx.ravel()
        df_dict['y'] = yy.ravel()
        df_dict['z'] = zz.ravel()
        df_dict['avg_temp'] = np.array([temp] * len(x) * len(y) * len(z))

        df = pd.DataFrame(data=df_dict)

        return df

    def _interpolate_data(self, data, resolution):
        """
        Replace data with a higher resolution interpolation
        Parameters
        ----------
        data
        resolution

        Returns
        -------
        interpolated_temps, (grid_x, grid_y, grid_z, grid_temps)
        """
        # TODO: review this function
        # import pdb; pdb.set_trace()
        if self.condition in 'controlControlCONTROL':
            return None  # TODO: wtf

        # useful aliases
        x, y, z, temps = data.x.values, data.y.values, data.z.values, data.avg_temp.values

        # calculate average 3D euclidean distance b/w observations
        avg_distance = self.calc_euclidean_distance_neighbords(selection = 'padded')


        # init rbf interpolator
        """smoothing was determined by testing various numbers and looking at the minimum and maximum of the resulting plumes
        if I put values too far from this, the minimum and maximum temperature start to become extremely unnaturalistic.
        """
        smoothing = 2e-5
        rbfi = Rbf(x, y, z, temps, function='quintic', smooth=smoothing, epsilon=avg_distance)

        # make positions to interpolate at
        # TODO: run this on a computer with lots of memory and save CSV so you don't run into memory errors (200, 60, 60)
        xi = np.linspace(self.downwind, self.upwind, 50)  # todo: fix resolution
        yi = np.linspace(self.left, self.right, 15)
        zi = np.linspace(self.floor, self.ceiling, 15)
        # xi = np.linspace(self.downwind, self.upwind, 25)  # todo: fix resolution
        # yi = np.linspace(self.left, self.right, 7)
        # zi = np.linspace(self.floor, self.ceiling, 7)
        # we save this grid b/c it helps us with the gradient func
        grid_x, grid_y, grid_z = np.meshgrid(xi, yi, zi, indexing='ij')
        grid_x_flat = grid_x.ravel()
        grid_y_flat = grid_y.ravel()
        grid_z_flat = grid_z.ravel()

        # interpolate
        interp_temps = rbfi(grid_x_flat, grid_y_flat, grid_z_flat)
        # we save this grid b/c it helps us with the gradient func
        grid_temps = interp_temps.reshape((len(xi), len(yi), len(zi)))

        # save to df
        df_dict = dict()
        df_dict['x'] = grid_x_flat
        df_dict['y'] = grid_y_flat
        df_dict['z'] = grid_z_flat
        df_dict['avg_temp'] = interp_temps
        interpolated_temps = pd.DataFrame(df_dict)

        return interpolated_temps, grid_x, grid_y, grid_z, grid_temps

    def _calc_gradient(self):
        # impossible to do gradient with uneven samples: https://stackoverflow.com/questions/36781698/numpy-sample-distances-for-3d-gradient
        # so doing instead on regular grid
        # TODO: review this gradient function
        if self.condition in 'controlControlCONTROL':
            return None

        # grid_x, grid_y, grid_z = np.meshgrid(xi, yi, zi, indexing='ij')
        #grid_temps = interp_temps.reshape((len(xi), len(yi), len(zi)))

        # Solve for the spatial
        distances = [np.diff(self.data.x.unique())[0], np.diff(self.data.y.unique())[0], np.diff(self.data.z.unique())[0]]
        gradient_x, gradient_y, gradient_z = np.gradient(self.grid_temp, *distances)

        self.data['gradient_x'] = gradient_x.ravel()
        self.data['gradient_y'] = gradient_y.ravel()
        self.data['gradient_z'] = gradient_z.ravel()

        self.data.fillna(0, inplace=True)  # replace NaNs, infs before calculating norm
        self.data.replace([np.inf, -np.inf], 0, inplace=True)

        self.data['gradient_norm'] = np.linalg.norm(self.data[['gradient_x', 'gradient_y', 'gradient_z']], axis=1)

        return gradient_x, gradient_y, gradient_z

    def _calc_kdtree(self, selection = 'interpolated'):
        if self.condition in 'controlControlCONTROL':
            return None

        data = self._select_data(selection)

        zdata = zip(data.x, data.y, data.z)
        return kdt(zdata)

    def _select_data(self, selection):
        if selection == 'raw':
            data = self._raw_data
        elif selection == 'padded':
            data = self.padded_data
        elif selection == 'interpolated':
            data = self. data
        else:
            raise ValueError

        return data


class UnaveragedPlume:
    def __init__(self, environment):
        super(self.__class__, self).__init__(environment)
        raise NotImplementedError  # TODO: implement unaveraged plume