# -*- coding: utf-8 -*-
"""
Flight trajectory plotting functions

Created on Fri Mar 20 12:27:04 2015
@author: Richard Decal, decal@uw.edu
https://staff.washington.edu/decal/
https://github.com/isomerase/
"""
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import itertools
from matplotlib.patches import Rectangle
import matplotlib.ticker as mtick
import seaborn as sns

sns.set_palette("muted", 8)


def plot_single_trajectory(dynamics, target_pos, detect_thresh, boundary, title="Individual trajectory", titleappend=""):
    # plot an individual trajectory
    plt.plot(dynamics['position x'], dynamics['position y'], lw=2, alpha=0.5)
    currentAxis = plt.gca()
    cage = draw_cage()
    currentAxis.add_patch(cage)
    currentAxis.axis([0,1,0.127, -0.127])
    if target_pos is not None:
        heaterCircle, detectCircle = draw_heaters(target_pos, detect_thresh)
        currentAxis.add_artist(heaterCircle)
        currentAxis.add_artist(detectCircle)
    plt.gca().set_aspect('equal')
    
    plt.title(title + titleappend, fontsize=20)
    plt.xlabel("$x$", fontsize=14)
    plt.ylabel("$y$", fontsize=14)


def draw_cage():
    cage_midX, cage_midY = 0.1524, 0.
    return plt.Rectangle((cage_midX - 0.0381, cage_midY - 0.0381), 0.0762, 0.0762, facecolor='none')
    

def draw_heaters(target_pos, detect_thresh):
    heaterCircle = plt.Circle((target_pos[0], target_pos[1],), 0.003175, color='r')  # 0.003175 is diam of our heater
    detectCircle = plt.Circle((target_pos[0], target_pos[1],), detect_thresh, color='gray', fill=False, linestyle='dashed')
    return heaterCircle, detectCircle


def trajectory_plots(ensemble, metadata, heatmap, trajectoryPlot=False):
    """"Plot all the trajectories into a single arena"""
    target_pos = metadata['target position']
    ensemble_len = max(metadata['trajectory number'])
    fig, ax = plt.subplots(1)
    sns.set_style("white")
#    for trajectory_i in metadata['trajectory number']:
#        posx = ensemble.xs(trajectory_i, level='trajectory')['position x']
#        if ensemble_len < 60:
#            alpha=0.4
#        else:
#            alpha=0.02
#        if trajectoryPlot is True:
#            print posx
#            posy = ensemble.xs(trajectory_i, level='trajectory')['position y']
#            ax.plot(posx, posy, lw=2, alpha=1)
#        ax.axis([0,1,0.127, -0.127])  # slight y padding for graphs
    title_append = r""" $T_max$ = {0} secs, $\beta = {2}$, $f = {3}$, $wtf = {4}$.
#                """.format(metadata['time max'], ensemble_len, metadata['beta'], metadata['rf'], metadata['wtf'])
#                
    # draw heater
    if metadata['target position'] is not None:
        heaterCircle, detectCircle = draw_heaters(metadata['target position'], metadata['detection threshold'])
        ax.add_artist(heaterCircle)
        ax.add_artist(detectCircle)
#    
    # draw cage
    cage = draw_cage()
    ax.add_patch(cage)
#
#    
    # plot shwag
    title_append = title_append + """<Tfind> = {0:}, Sourcefinds = {1}/(n = {2})""".format( metadata['time to target find average'], metadata['N targets found'], ensemble_len)
    plt.title("Agent trajectories" + title_append, fontsize=14)
    plt.xlabel("$x$", fontsize=14)
    plt.ylabel("$y$", fontsize=14)
    plt.axis(metadata['boundary'])
    sns.set_style("white")
#    
    # save before overlaying heatmap
    plt.savefig("./figs/Trajectories b{beta} f{rf} wf{wtf} bounce {bounce} N{total_trajectories}.png"\
        .format(beta=metadata['beta'], rf=metadata['rf'], wtf=metadata['wtf'], bounce=metadata['bounce'], total_trajectories=ensemble_len))
#    
    ## Position heatmap
    if heatmap is True:
        # crunch the data
        counts, xedges, yedges = np.histogram2d(ensemble['position x'], ensemble['position y'], bins=(100,30), range=[[0, 1], [-0.15, .15]])
        
        # counts needs to be transposed to use pcolormesh     
        counts = counts.T
        
        MaxVal = ensemble_len/2
        if ensemble_len > 100:
            plt.cla()
        heatmap = ax.pcolormesh(xedges, yedges, counts, cmap=plt.cm.Oranges, vmin=0, vmax=MaxVal)
#        plt.gca().invert_yaxis()  # hack to match y axis convention --- now unneeded?
        ax.set_ylim(metadata['boundary'][2:])
        
        # overwrite previous plot schwag
        cbar = plt.colorbar(heatmap)
        cbar.ax.set_ylabel('Counts')
        plt.title("Agent Trajectories Heatmap (n = {})".format(ensemble_len))
        plt.xlabel("$x$")
        plt.ylabel("$y$")
        plt.savefig("./figs/Trajectories heatmap beta{beta}_f{rf}_wf{wtf}_bounce {bounce} N{total_trajectories}.png".format(beta=metadata['beta'], rf=metadata['rf'], wtf=metadata['wtf'], bounce=metadata['bounce'], total_trajectories=ensemble_len))
        plt.show()


def stateHistograms(ensemble, metadata):
    fig = plt.figure(4, figsize=(9, 8))
    gs1 = gridspec.GridSpec(2, 2)
    axs = [fig.add_subplot(ss) for ss in gs1]
    fig.suptitle("Agent Model Flight Distributions", fontsize=14)
    ensemble_len = max(metadata['trajectory number'])
    
    # position distributions
#    pos_all = np.concatenate(pos, axis=0)
    pos_binwidth = .01
    
    # X pos
    xpos_min, xpos_max = 0., 1.
    xpos_counts, xpos_bins = np.histogram(ensemble['position x'], bins=np.linspace(xpos_min, xpos_max, (xpos_max-xpos_min) / pos_binwidth))
    xpos_counts_n = xpos_counts.astype(int) / float(xpos_counts.size)
    axs[0].plot(xpos_bins[:-1]+pos_binwidth/2, xpos_counts_n, lw=2)
    axs[0].bar(xpos_bins[:-1], xpos_counts_n, xpos_bins[1]-xpos_bins[0], facecolor='blue', linewidth=0, alpha=0.1)
    axs[0].set_title("Upwind ($x$) Position Distributions", fontsize=12)
    axs[0].set_xlabel("Position ($m$)")
    axs[0].set_ylabel("Probability")
    
    # Y pos
    ypos_min, ypos_max = -0.15, 0.15
    ypos_counts, ypos_bins = np.histogram(ensemble['position y'], bins=np.linspace(ypos_min, ypos_max, (ypos_max-ypos_min)/pos_binwidth))
    ypos_counts_n = ypos_counts/ ypos_counts.astype(float).sum()
    axs[1].plot(ypos_bins[:-1]+pos_binwidth/2, ypos_counts_n, lw=2)
    axs[1].set_xlim(ypos_min+pos_binwidth/2, ypos_max-pos_binwidth/2)  # hack to hide gaps
    axs[1].fill_between(ypos_bins[:-1]+pos_binwidth/2, 0, ypos_counts_n, facecolor='blue', alpha=0.1)
    axs[1].set_title("Cross-wind ($y$) Position Distributions")
    axs[1].set_xlabel("Position ($m$)")
    axs[1].set_ylabel("Probability")
    

    ## Velo distributions
    vmin, vmax = -1.0, 1.
    velo_bindwidth = 0.02
    
    # vx component
    vx_counts, vx_bins = np.histogram(ensemble['velocity x'], bins=np.linspace(vmin, vmax, (vmax-vmin)/velo_bindwidth))
    vx_counts_n = vx_counts / vx_counts.astype(float).sum()
    axs[2].plot(vx_bins[:-1], vx_counts_n, label="$\dot{x}$")
    axs[2].fill_between(vx_bins[:-1], 0, vx_counts_n, facecolor='blue', alpha=0.1)
    # vy component
    vy_counts, vy_bins = np.histogram(ensemble['velocity y'], bins=np.linspace(vmin, vmax, (vmax-vmin)/velo_bindwidth))
    vy_counts_n= vy_counts / vy_counts.astype(float).sum()
    axs[2].plot(vy_bins[:-1], vy_counts_n, label="$\dot{y}$")
    axs[2].fill_between(vy_bins[:-1], 0, vy_counts_n, facecolor='green', alpha=0.1)
    # |v|
    velo_all_magn = []
#    for v in velo_all:
#        velo_all_magn.append(np.linalg.norm(v))
#    vabs_counts, vabs_bins = np.histogram(velo_all_magn, bins=np.linspace(vmin, vmax, (vmax-vmin)/velo_bindwidth))
#    vabs_counts_n = vabs_counts / vabs_counts.astype(float).sum()
#    axs[2].plot(vabs_bins[:-1], vabs_counts_n, label='$|\mathbf{v}|$', color=sns.desaturate("black", .4), lw=2)
#    axs[2].fill_between(vabs_bins[:-1], 0, vabs_counts_n, facecolor='yellow', alpha=0.1)
    
    axs[2].set_title("Velocity Distributions")
    axs[2].set_xlabel("Velocity ($m/s$)", fontsize=12)
    axs[2].set_ylabel("Probability", fontsize=12)
    axs[2].legend(fontsize=14)
    
    ## Acceleration distributions
#    accel_all = np.concatenate(accels, axis=0)
    
    amin, amax = -10., 10
    accel_binwidth = 0.2
    
    # ax component
    ax_counts, ax_bins = np.histogram(ensemble['acceleration x'], bins=np.linspace(amin, amax, (amax-amin)/accel_binwidth))
    ax_counts_n = ax_counts / ax_counts.astype(float).sum()
    axs[3].plot(ax_bins[:-1], ax_counts_n, label="$\ddot{x}$", lw=2)
    axs[3].fill_between(ax_bins[:-1], 0, ax_counts_n, facecolor='blue', alpha=0.1)
    # ay component
    ay_counts, ay_bins = np.histogram(ensemble['acceleration y'], bins=np.linspace(amin, amax, (amax-amin)/accel_binwidth))
    ay_counts_n = ay_counts / ay_counts.astype(float).sum()
    axs[3].plot(ay_bins[:-1], ay_counts_n, label="$\ddot{y}$", lw=2)
    axs[3].fill_between(ay_bins[:-1], 0, ay_counts_n, facecolor='green', alpha=0.1)
    # |a|
#    accel_all_magn = []
#    for a in accel_all:
#        accel_all_magn.append(np.linalg.norm(a))
#    aabs_counts, aabs_bins = np.histogram(accel_all_magn, bins=np.linspace(amin, amax, (amax-amin)/accel_binwidth))
#    aabs_counts_n = aabs_counts/ aabs_counts.astype(float).sum()
#    axs[3].plot(aabs_bins[:-1], aabs_counts_n, label='$|\mathbf{a}|$', color=sns.desaturate("black", .4), lw=2)
#    axs[3].fill_between(aabs_bins[:-1], 0, aabs_counts_n, facecolor='yellow', alpha=0.1)
    axs[3].set_title("Acceleration Distribution")
    axs[3].set_xlabel("Acceleration ($m^s/s$)")
    axs[3].set_ylabel("Probability")
    axs[3].legend(fontsize=14)


    gs1.tight_layout(fig, rect=[0, 0.03, 1, 0.95])  # overlapping text hack
    plt.savefig("./figs/Agent Distributions b {beta},f {rf},wf {wtf},bounce {bounce},N {total_trajectories}.png".format(beta=metadata['beta'], rf=metadata['rf'], wtf=metadata['wtf'], bounce=metadata['bounce'], total_trajectories=ensemble_len))
    
    
#    # plot Forces
##    f, axes = plt.subplots(2, 2, figsize=(9, 9), sharex=True, sharey=True)
###    forcefig = plt.figure(5, figsize=(9, 8))
###    gs2 = gridspec.GridSpec(2, 2)
###    Faxs = [fig.add_subplot(ss) for ss in gs2]
##    forcefig = plt.figure(5)
##    Faxs1 = forcefig.add_subplot(211)
##    Faxs2 = forcefig.add_subplot(212)
#    g = sns.JointGrid("x", "y", (ensemble['totalF x'], ensemble['totalF y']), space=0)
#    g.plot_marginals(sns.kdeplot, shade=True)
#    g.plot_joint(sns.kdeplot, shade=True, cmap="PuBu", n_levels=40)
##    cmap = sns.cubehelix_palette(start=0, light=1, as_cmap=True)
##    sns.jointplot(np.array(ensemble['totalF x']), np.array(ensemble['totalF y']), ax=axes.flat[0], kind='kde', cmap=cmap, shade=True, cut = 5)
##    Faxs1.set_xlim(min(ensemble['totalF x']), max(ensemble['totalF x']))
##    Faxs1.set_ylim(min(ensemble['totalF y']), max(ensemble['totalF y']))
##    Faxs1.set_title("Total Forces")
##    Faxs1.set_aspect('equal')
##    Faxs1.set_xlabel("upwind")
##    Faxs1.set_ylabel("crosswind")
##    Faxs1.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.1e'))
##    Faxs1.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1e'))
#    
##    Faxs2.scatter(ensemble['wallRepulsiveF x'], ensemble['wallRepulsiveF y'])  
##    Faxs2.set_xlim(min(ensemble['wallRepulsiveF x']), max(ensemble['wallRepulsiveF x']))
##    Faxs2.set_ylim(min(ensemble['wallRepulsiveF y']), max(ensemble['wallRepulsiveF y']))
##    Faxs2.set_title("Wall Repulsion Forces")
##    Faxs2.set_xlabel("upwind")
##    Faxs2.set_ylabel("crosswind")
##    Faxs1.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.1e'))
##    Faxs2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1e'))
#    
#    plt.suptitle("Forces scatterplots")
#
#    
##    
##        ensemble['randF x'] = []
##    ensemble['randF y'] = []
##    ensemble['upwindF x'] = []
##    ensemble['upwindF y'] = []
#    
#    plt.tight_layout(pad=1.3)
#    plt.draw()
    
    
    
    return xpos_counts_n, ypos_bins, ypos_counts, ypos_counts_n, vx_counts_n


if __name__ == '__main__':
    import trajectory_stats
    
        # wallF params
    wallF_max=5e-7
    decay_const = 250
    
    # center repulsion params
    b = 4e-1  # determines shape
    shrink = 5e-7  # determines size/magnitude
    
    wallF = (b, shrink, wallF_max, decay_const)
    
    ensemmble, metadata = trajectory_stats.main(total_trajectories=400, plotting = False, wallF=wallF)
        
    trajectory_plots(ensemble, metadata, heatmap=True, trajectoryPlot = True)
    xpos_counts_n, ypos_bins, ypos_counts, ypos_counts_n, vx_counts_n = stateHistograms(ensemble, metadata)