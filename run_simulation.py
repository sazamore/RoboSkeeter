__author__ = 'richard'

import agent

N_TRAJECTORIES = 15  # set to zero to disable wall attraction
BOUNDED = True
INITIAL_POS = 'downwind_high'
COLLISION_TYPE = 'elastic'
# COLLISION_TYPE = 'crash'

agent_kwargs = {'initial_position_selection': 'downwind_high',
                'windF_strength': 0.,
                'randomF_strength': 6.55599224e-06,
                'experimental_condition': None,  # {'Left', 'Right', None}
                'stimF_stength': 0.,
                'spring_const': 0,
                'damping_coeff': 3.63674551e-07,
                'time_max': 15.,
                'bounded': True,
                'collision_type': 'crash',
                'crash_coeff': 0.8
                }

simulation, skeeter = agent.gen_objects_and_fly(N_TRAJECTORIES, agent_kwargs)

print "\nDone."

######################### plotting methods
# simulation.plot_3Dtrajectory(0)  # plot ith trajectory in the ensemble of trajectories

# print pd.isnull(simulation.data).any().nonzero()[0]
# print

# simulation.plot_kinematic_hists()
# simulation.plot_position_heatmaps()
# simulation.plot_force_violin()  # TODO: fix Nans in arrays

######################### dump data for csv for Sharri
# print "dumping to csvs"
# e = simulation.data
# r = e.trajectory_num.iloc[-1]
#
# for i in range(r+1):
#     e1 = e.loc[e['trajectory_num'] == i, ['position_x', 'position_y', 'position_z', 'inPlume']]
#     e1.to_csv("l"+str(i)+'.csv', index=False)
#
# # simulation.plot_kinematic_hists()
# # simulation.plot_posheatmap()
# # simulation.plot_force_violin()
#
# # # for plume stats
# # g = e.loc[e['behavior_state'].isin(['Left_plume Exit left', 'Left_plume Exit right', 'Right_plume Exit left', 'Right_plume Exit right'])]

#
# ######################### manual scoring
# from score import *
# import scripts
#
# experimental_bins, experimental_vals = scripts.pickle_experiments.load_mosquito_kdes()
#
# targ_ensemble = simulation
#
# targ_data = get_data(targ_ensemble)
# targ_KDEs = calc_kde(targ_data)
# targ_vals = evaluate_kdes(targ_KDEs, experimental_bins)  # we evaluate targ KDE at experimental vins for comparison
#
#
# # solve DKL b/w target and reference trajectories
# dkl_v_x = entropy(targ_vals['v_x'], qk=experimental_vals['v_x'])
# dkl_v_y = entropy(targ_vals['v_y'], qk=experimental_vals['v_y'])
# dkl_v_z = entropy(targ_vals['v_z'], qk=experimental_vals['v_z'])
# dkl_a_x = entropy(targ_vals['a_x'], qk=experimental_vals['a_x'])
# dkl_a_y = entropy(targ_vals['a_y'], qk=experimental_vals['a_y'])
# dkl_a_z = entropy(targ_vals['a_z'], qk=experimental_vals['a_z'])
# dkl_c = entropy(targ_vals['c'], qk=experimental_vals['c']) * 6.  # scaled up by 6 to increase relative importance
#
# dkl_scores = [dkl_v_x, dkl_v_y, dkl_v_z, dkl_a_x, dkl_a_y, dkl_a_z, dkl_c]
# for i, val in enumerate(dkl_scores):
#     if val > 20:
#         dkl_scores[i] = 20.
# dkl_score = sum(dkl_scores)
