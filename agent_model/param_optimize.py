__author__ = 'richard'

import agent3D
import plume3D
import trajectory3D
from scipy.optimize import basinhopping
import numpy as np
from matplotlib import pyplot as plt
import logging
from scipy.stats import entropy
from datetime import datetime
import acfanalyze

logging.basicConfig(filename='basin_hopping.log',level=logging.DEBUG)

myplume = plume3D.Plume(None)

# load csv values
a_csv = np.genfromtxt('experimental_data/acceleration_distributions_uw.csv',delimiter=',')
a_csv = a_csv.T
a_observed = a_csv[4][:-1]  # throw out last datum

v_csv = np.genfromtxt('experimental_data/velocity_distributions_uw.csv',delimiter=',')
v_csv = v_csv.T
v_observed = v_csv[4][:-1]  # throw out last datum

# wrapper func for agent 3D
def wrapper(GUESS, N_trajectories):
    """
    :param bias_scale_GUESS:
    :param mass_GUESS:
        mean mosquito mass is 2.88e-6
    :param damping_GUESS:
        estimated damping was 5e-6, # cranked up to get more noise #5e-6,#1e-6,  # 1e-5
    :return:
    """
    BETA, FORCES_AMPLITUDE, F_WIND_SCALE = GUESS
    HEATER = None
    K = 0  # no wall force for optimization
    # F_WALL_SCALE aka k

#    beta_prime, bias_scale_GUESS = param_vect
    # when we run this, agent3D is run and we return a score

    plume_object = plume3D.Plume(HEATER)  # we are fitting for the control condition
    # temperature plume
    trajectories = trajectory3D.Trajectory() # instantiate empty trajectories object
    skeeter = agent3D.Agent(
        trajectories,
        plume_object,
        mass=2.88e-6,
        agent_pos="downwind_plane",
        heater=HEATER,
        wtf=F_WIND_SCALE,
        F_amplitude=FORCES_AMPLITUDE,
        stimF_str=0., # F_STIM_SCALE,
        beta=BETA,
        k=K, #
        Tmax=15.,
        dt=0.01,
        detect_thresh=0.023175,
        bounded=True)

    skeeter.fly(total_trajectories=N_trajectories, verbose=False)  # fix N trajectories in main

    # ensemble = trajectories.ensemble
    # # trimmed_ensemble = ensemble.loc[
    # #     (ensemble['position_x'] >0.25) & (ensemble['position_x'] <0.95)]

    # we want to fit beta and rF
    score = error_fxn(trajectories.ensemble, GUESS)

    # end = time.time()
    # print end - start
    # print "Guess: ", GUESS, "Score: ", score
    return score


def error_fxn(ensemble, guess):
    # compare ensemble to experiments, return score to wrapper

    # get histogram vals for agent ensemble
    adist = 0.1
    # |a|
    amin, amax = 0., 4.9+adist  # arange drops last number, so pad range by dist
    # pdb.set
    accel_all_magn = ensemble['acceleration_3Dmagn'].values
    a_counts, aabs_bins = np.histogram(accel_all_magn, bins=np.arange(amin, amax, adist))
    # turn into prob dist
    a_counts = a_counts.astype(float)
    a_total_counts = a_counts.sum()
    a_counts_n = a_counts / a_total_counts
    # print a_counts_n

    # solve DKL
    dkl_a = entropy(a_counts_n, qk=a_observed)

    vdist =  0.015
    vmin, vmax = 0., 0.605
    velo_all_magn = ensemble['velocity_3Dmagn'].values
    v_counts, vabs_bins = np.histogram(velo_all_magn, bins=np.arange(vmin, vmax, vdist))
    v_counts = v_counts.astype(float)
    v_total_counts = v_counts.sum()
    # turn into prob dist
    v_counts_n = v_counts / v_total_counts

    # solve DKL
    dkl_v = entropy(v_counts_n, qk=v_observed)
    # print 'dkl_v' , dkl_v


    dkl_score = dkl_a + dkl_v
    # final_score = dkl_v

    ################ ACF metrics############
    global ACF_THRESH
    global N_TRAJECTORIES

    acf_distances = []
    for i in range(N_TRAJECTORIES):
        df = ensemble.loc[ensemble['trajectory_num']==i]
        acf_threshcross_index = acfanalyze.index_drop(df, thresh=ACF_THRESH, verbose=False)
        if acf_threshcross_index is 'explosion':  # bad trajectory!
            acf_distances.append(300)
        else:
            distance = sum(abs( acf_threshcross_index - np.array([16., 16., 10.]) ))
            acf_distances.append(distance)

    acf_mean = np.mean(acf_distances)
    # print "mean", acf_mean
    acf_score = np.log(acf_mean+1)
    # print "score", acf_score

    final_score = dkl_score + acf_score


    if np.isnan(final_score):
        final_score = 0
    global HIGH_SCORE
    if final_score < HIGH_SCORE:
        HIGH_SCORE = final_score
        print "{} New high score: {}. Guess: {}. DKL score = {}. ACF score = {}".format(datetime.now(), HIGH_SCORE, guess, dkl_score, acf_score)
        logging.info("Bingo! New high score: {}. Guess: {}".format(HIGH_SCORE, guess))

        global PLOTTER
        if PLOTTER is True:
            plt.ioff()
            f, axarr = plt.subplots(2, sharex=False)
            axarr[0].plot(aabs_bins[:-1], a_counts_n, label='RoboSkeeter')
            axarr[0].plot(aabs_bins[:-1], a_observed, c='r', label='experiment')
            axarr[0].set_title('accel score=> {}. High score = DKL(a)+DKL(v) = {}'.format(dkl_a, HIGH_SCORE))
            axarr[0].legend()

            axarr[1].plot(vabs_bins[:-1], v_counts_n, label='RoboSkeeter')
            axarr[1].plot(vabs_bins[:-1], v_observed, c='r', label='experiment')
            axarr[1].set_title('velocity score=> {}. High score = DKL(a)+DKL(v) = {}'.format(dkl_v, HIGH_SCORE))
            axarr[1].legend()
            plt.suptitle('Parameter Guess: {}'.format(guess))
            plt.show()
            plt.close()

    return final_score

# # for nelder mead
# Nfeval = 1
# def callbackF(guess1, guess2, guess3):
#      global Nfeval
#      print '{0:4d}   {1: 3.25f}   {2: 3.25f}   {3: 3.8f}'.format(Nfeval, Xi[0], Xi[1], wrapper(Xi))
#      Nfeval += 1

# # for basin hopping
# Nfeval = 1
# def callbackF(Xi, score, accept):
#     global Nfeval
#     print '{0:4d}  |  Basin found at: {1}  | Score: {2: 3.10f}  | Accepted: {3}'.format(Nfeval, Xi, score, accept)
#     Nfeval += 1


def main():
    global HIGH_SCORE
    HIGH_SCORE = 1e10
    OPTIM_ALGORITHM = 'SLSQP'

    global PLOTTER
    PLOTTER = False

    global ACF_THRESH
    ACF_THRESH = 0.5
#    result = minimize(
#        wrapper,
#        [1e-5, 4e-5],
#        method='Nelder-Mead',
#        #bounds=((1e-8, 1e-4), (1e-6, 1e-3)),
#        options={'xtol': 1e-7, 'disp':True},
#        callback=callbackF)

    # result = fminbound(
    #     wrapper, # bias_scale_GUESS, mass_GUESS, damping_GUESS)
    #     np.array([100, 200, 100]),
    #     np.array([1000, 1000, 1000]),
    #     xtol=100,
    #     full_output=True,
    #     disp=3)

    print "Starting optimizer."

    guess_params = "[BETA, FORCES_AMPLITUDE, F_WIND_SCALE]"  # [5e-6, 4.12405e-6, 5e-7]
    INITIAL_GUESS = [  1.37213380e-06 ,  1.39026239e-06 ,  2.06854777e-06]
    global  N_TRAJECTORIES
    N_TRAJECTORIES = 20

    logging.info("""\n ############################################################
    ############################################################
    {} Start optimization with {} algorithm
    # trajectories = {}
    Params = {}
    Initial Guess = {}
    ############################################################""".format(
        datetime.now(), OPTIM_ALGORITHM, N_TRAJECTORIES, guess_params, INITIAL_GUESS))

    result = basinhopping(
        wrapper,
        INITIAL_GUESS,
        # stepsize=1e-5,
        T=1e-4,
        minimizer_kwargs={"args": (N_TRAJECTORIES,), 'method': OPTIM_ALGORITHM},  # bounds were  "bounds": ((200, 1000),(255,1000),(200,1000))
        # callback=callbackF,
        disp=True
        )

    return result
    # fminbound(wrapper, )
    # wrapper(1e-7)


if __name__ == '__main__':
    result = main()


    logging.info("""############################################################
    Trial end. FINAL RESULT: {}
    ############################################################""".format(result))

    print result