__author__ = 'richard'
import numpy as np

def calculate_heading(velo_x_component, velo_y_component):
    theta = np.arctan2(velo_y_component, velo_x_component)

    return theta*180/np.pi


def calculate_angular_velocity(velocity_vec):
    #
    pass # TODO: https://en.wikipedia.org/wiki/Angular_velocity#Particle_in_three_dimensions


def calculate_curvature(ensemble):
    """using formula from https://en.wikipedia.org/wiki/Curvature#Local_expressions_2"""
    velocity_vec = np.vstack((ensemble.velocity_x, ensemble.velocity_y, ensemble.velocity_z))  # shape is (3, R)
    acceleration_vec = np.vstack((ensemble.acceleration_x, ensemble.acceleration_y, ensemble.acceleration_z))

    numerator = np.linalg.norm( np.cross(velocity_vec.T, acceleration_vec.T), axis=1)
    denominator = np.linalg.norm(acceleration_vec, axis=0)** 3

    return numerator/denominator


def gen_symm_vecs(dims=3):
    """generate randomly pointed (radially-symmetric) 3D unit vectors/ direction vectors

    first we draw from a 3D gaussian, which is a symmetric distribution no matter how you slice it. then, we map
    those draws onto the unit sphere.

    credit: http://codereview.stackexchange.com/a/77945/76407
    """
    vecs = np.random.normal(size=dims)
    mags = np.linalg.norm(vecs, axis=-1)

    ends = vecs / mags[..., np.newaxis]  # divide by length to get unit vector

    return ends


def calc_polar_kinematics(ensemble):
    """append polar kinematics to ensemble"""
    field_list = ['velocity', 'acceleration', 'randomF', 'wallRepulsiveF', 'upwindF', 'stimF']
    for name in field_list:
        x_component, y_component = ensemble[name+'_x'], ensemble[name+'_y']
        angle = np.arctan2(y_component, x_component)
        angle[angle < 0] += 2*np.pi  # get vals b/w [0,2pi]
        eval(name+'_xy_theta = angle')
        ensemble[name+'_xy_mag'] = np.sqrt(y_component**2 + x_component**2)

    return array_dict

def check_turning():
    pass
"""            # # turning state
            # if tsi in [0, 1]:
            #     V['turning'][tsi] = 0
            # else:
            #     turn_min = 3
            #     if abs(V['velocity_angular'][tsi-turn_min:tsi]).sum() > self.turn_threshold*turn_min:
            #         V['turning'][tsi] = 1
            #     else:
            #         V['turning'][tsi] = 0"""