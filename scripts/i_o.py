# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 17:21:42 2015

@author: richard
"""
import os
import pandas as pd
import numpy as np
import csv
from glob import glob
from Tkinter import Tk
from tkFileDialog import askdirectory

    
def load_experiment_csv(file_path):
    """loads csv as-is"""
#    file_path = os.path.join(script_dir, rel_data_path, filename)
    return pd.read_csv(file_path, header=None, na_values="NaN")
    

def load_histogram_csv(filepath):
    pass


def save_processed_csv(trajectory_list, filepath):
    """Outputs x,y,z coords at each timestep to a csv file. These trajectories
    will still contain short NaN repeats, but Sharri will fix that downstream
    using her interpolating code. She will also Kalman filter.
    """
    dir = os.path.dirname(filepath)
    filename, extension = os.path.splitext ( os.path.basename(filepath) )
    for i, trajectory in enumerate(trajectory_list):
        trajectory = trajectory.fillna("NaN")  # hack to turn nan into string 
        # so that the csv doesn't have empty fields
        file_path = os.path.join(dir, "Processed/", filename + "_SPLIT_" + str(i))
        trajectory.to_csv(file_path, index=False)
        
        
def load_csv2DF(data_fname, rel_dir = "data/processed_trajectories/"):
    file_path = os.path.join(os.getcwd(), rel_dir, data_fname + ".csv")

    col_labels = [
        'position_x',
        'position_y',
        'position_z',
        'velocity_x',
        'velocity_y',
        'velocity_z',
        'acceleration_x',
        'acceleration_y',
        'acceleration_z',
        'heading_angle',
        'angular_velo_xy',
        'angular_velo_yz',
        'curvature'
    ]

    dataframe = pd.read_csv(file_path, na_values="NaN", names=col_labels)  # recognize str(NaN) as NaN
    dataframe.fillna(value=0, inplace=True)

    return dataframe

def load_CSVdir_to_trajectory(relative_dir):
    import trajectory
    t = trajectory.Trajectory()
    t.load_experiments(relative_dir=relative_dir)
    return t


def load_csv2np():
    v_csv = np.genfromtxt(os.path.join(os.path.dirname(__file__),'experiments','velocity_distributions_uw.csv'), delimiter=',')
    v_csv = v_csv.T
    v_observed = v_csv[4][:-1]  # throw out last datum

    # load csv values
    a_csv = np.genfromtxt(os.path.join(os.path.dirname(__file__),'experiments','acceleration_distributions_uw.csv'), delimiter=',')
    a_csv = a_csv.T
    a_observed = a_csv[4][:-1]  # throw out last datum

    return  v_observed, a_observed


def get_csv_name_list(path, relative=True):
    if relative:
        return os.listdir(os.path.join(os.path.realpath('.'), path))
    else:
        return os.listdir(path)

def get_csv_filepath_list(path, csv_list):
    paths = [os.path.join(path, fname) for fname in csv_list]
    return paths

def get_directory():
    Tk().withdraw()
    directory = askdirectory()
    print("Selected dir {}".format(directory))
    return directory

if __name__ == '__main__':
    a = load_csv2DF('Control-27')