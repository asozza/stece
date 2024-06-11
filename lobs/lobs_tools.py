#!/usr/bin/env python3

###############################################################################
###############################################################################
# 
# LOBSTER: Load balancing script for ec-earth4
# -----------------------------------------------------------------------------
# Functions and tools
# 
# Author: A. Sozza (2024)
#
###############################################################################
###############################################################################

import sys
import os
import re
import time
import math
import yaml
import numpy as np
import matplotlib.pyplot as plt

########################################################
# Searching by patterns

# search for values preceded by label
def read_value_preceded_by_label(file_path, label):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                pattern = fr'{label}\s*[:=]?\s*(\d+(?:\.\d+)?)'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value= float(match.group(1))
                    return value
        # if label is not found
        return None
    except FileNotFoundError:
        print(path_file," not found")
        return None

# search for values followed by label
def read_value_followed_by_label(file_path, label):
    try:
        with open(file_path, 'r') as file:
            for	line in	file:
                pattern = fr'(\d+(?:\.\d+)?)\s*[^0-9a-zA-Z]*{label}[^0-9a-zA-Z]*\s*[:=]?'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value= float(match.group(1))
                    return value
        # if label is not found
        return None
    except FileNotFoundError:
        print(path_file," not found")
        return None

# search for value constrained by two labels
def read_value_constrained_by_two_labels(file_path, label):
    try:
        start_search = False
        with open(file_path, 'r') as file:
            for line in file:
                pattern = fr"Load balance analysis"
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    start_search = True                    
                if  start_search:
                    parts = line.strip().split('/')
                    if len(parts) == 3 and parts[0].strip() == label:
                        value1 = float(parts[1].strip())
                        value2 = float(parts[2].strip())
                        return value1, value2
        # if label is not found
        return None, None
    except FileNotFoundError:
        print(path_file," not found")
        return None, None

# search for value below a label
def read_value_below_a_label(file_path, label):
    try:
        start_search = False
        with open(file_path, 'r') as file:
            for line in file:
                if start_search and line.strip().startswith(':'):
                    value = float(line.split(':')[1].strip())
                    return value
                if label in line:
                    start_search = True                    
        # if label is not found
        return None
    except FileNotFoundError:
        print(path_file," not found")
        return None

# read time (in format hh:mm:ss) preceded by label
def read_time_preceded_by_label(file_path, label):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                pattern = fr'{label}:\s*(\d+):(\d+):(\d+\.\d+)'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    seconds = float(match.group(3))
                    return hours, minutes, seconds
        # if label is not found
        return None, None, None
    except FileNotFoundError:
        print(file_path, " not found")
        return None, None, None

#############################################################
# i/o operations
    
def read_path():

    # read from yaml file
    with open('paths.yaml') as jf:
        config = yaml.load(jf, Loader=yaml.FullLoader)
    if 'folders' in config:
        folders = config['folders']
    mainpath = folders.get('path', '')

    return mainpath

def folders(mainpath, expname): 

    dirs = {
        'exp': os.path.join(mainpath, expname),
        'log': os.path.join(mainpath, expname, "log"),
    }

    return dirs


############################################################
# Variables

def compute_vars(dirs, leg):

    var = np.zeros(7)

    # nprocs
    path = os.path.join(dirs['log'], leg, 'NODE.001_01')
    var[0] = read_value_preceded_by_label(path, 'NPROC') # nprocs of oifs, npa    
    path = os.path.join(dirs['log'], leg, 'ocean.ouput')
    var[1] = read_value_preceded_by_label(path, 'jpnij') # nprocs of nemo, npo
    nptot = var[0]+var[1]+1 # total nprocs
    
    # times
    path = os.path.join(dirs['log'], leg, 'timing.log')
    hours, minutes, seconds = read_time_preceded_by_label(path, 'elapsed time')    
    var[2] = read_value_followed_by_label(path, 'SYPD') # simulated year per day, sypd
    var[3] = 24./var[2] # simulated year per hour, syph
    var[4] = var[3]*nptot # core-hours per simulated year, chpsy
    var[5] = hours*3600.+minutes*60.+seconds # elapsed time
    var[6] = nptot*var[5]*470410408./(86400.*8098.*128.) # system billing units, sbu

    return var #npa,npo,sypd,syph,chpsy,elapsedtime,sbu

def compute_nprocs(dirs, leg):

def multiple_legs(dirs, legs):

    #append
    vars = []
    for leg in range(1,legs):
        x = compute_vars(dirs, leg)
        vars = np.append(vars, x)

    return vars

def multiple_runs(dirs, legs):

    #append
    vars = []

    return vars

def organize_by_nodes():

    # total procs and nodes
    nptot = vars[2]+vars[1]+1
    nodes = np.ceil(nptot/128).astype(int)
    # sort unique nodes in ascending order
    unique_nodes = set(nodes)
    sorted_nodes = sorted(unique_nodes)

    return sorted_nodes

#############################################################
# Outputs: plots and tables

def plot_singlerun(expname, xvar, yvar):

    pp = plt.plot(xvar, yvar)

    return pp

def plot_multirun(expname, xvar, yvar):

    pp = plt.plot(xvar, yvar)

    return pp

def save_table(simulations):

    # sort vectors based on oifs/nemo fraction
    vectors = [ nodes, nfrac, npa, npo, sypd, syph, chpsy, elapsedtime, sbu ]
    sorted_indices = np.argsort(nfrac)
    sorted_vectors = [vector[sorted_indices] for vector in vectors]
    sorted_simulations = [simulations[i] for i in sorted_indices]

    # write output
    with open('recap.txt', 'w') as file:
        print('# nodes(1) npo/npa(2) npa(3) npo(4) tsa(5) cta(6) wta(7) tso(8) cto(9) wto(10) tsr(11) ctr(12) wtr(13) sypd(14) syph(15) chpsy(16) elapsed_time(17) sbu(18) ', file=file)
        print('# ', file=file)
        for node in sorted_nodes:
            print('', file=file)
            print(f'# N={node}', file=file)
            for i in range(len(simulations)):
                if sorted_vectors[0][i] == node: # checkes nodes[i]
                    row = [f"{vector[i]:<5}" for vector in sorted_vectors]
                    row.append(f"({sorted_simulations[i]})")
                    print(" ".join(row), file=file)
        print('', file=file)

