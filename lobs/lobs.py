#!/usr/bin/env python3

###############################################################################
# 
# LOBS: Load Balancing Script
# ---------------------------------------
# Input: + log files:
#             - load_balancing_info.txt
#             - ocean.output
#             - NODE.001_01
#             - timing.log
#
# Output: + recap.txt
# 
# Author: A. Sozza (2023)
#
###############################################################################
# 
# yam file:
# ---
# folders:
# - path: /ec/res4/hpcperm/itas/runs
#  simulations: [ oass, oasx, oasr, oasp, oasy, oast, oasu, oasw, oasv, oasz ]
#
###############################################################################


import sys
import os
import time
import re
import numpy as np
import math
import yaml

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

# read elapsed time
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
    
###############################################################################
############################################################################### 
# MAIN SCRIPT

# read from yaml file
with open('paths.yaml') as jf:
    config = yaml.load(jf, Loader=yaml.FullLoader)

if 'folders' in config:
    folders = config['folders']
    
for ifo in folders:
    path = ifo.get('path', '')
    simulations = ifo.get('simulations', [])
    simulation_paths = [path + '/' + simulation for simulation in simulations]


# read processors
file_name = 'log/001/NODE.001_01'
file_paths = [sim_path + '/' + file_name for sim_path in simulation_paths]
label = 'NPROC'
npa = np.array([])
for file_path in file_paths:
    value = read_value_preceded_by_label(file_path, label)
    npa = np.append(npa, value)
    
file_name = 'log/001/ocean.output'
file_paths = [sim_path + '/' + file_name for sim_path in simulation_paths]
label = 'jpnij'
npo = np.array([])
for file_path in file_paths:
    value = read_value_preceded_by_label(file_path, label)
    npo = np.append(npo, value)    


# oifs/nemo procs fraction
nfrac = npo/npa
# total procs and nodes
nptot = npo+npa+1
nodes = np.ceil(nptot/128).astype(int)
# sort unique nodes in ascending order
unique_nodes = set(nodes)
sorted_nodes = sorted(unique_nodes)


# read timing
file_name = 'log/001/timing.log'
file_paths = [sim_path + '/' + file_name for sim_path in simulation_paths]
sypd = np.array([])
elapsed_time = np.array([])
for file_path in file_paths:
    label='elapsed time'
    hours, minutes, seconds = read_time_preceded_by_label(file_path, label)
    elapsed_time = np.append(elapsed_time,hours*3600.+minutes*60.+seconds)
    label = 'SYPD'
    value = read_value_followed_by_label(file_path, label)
    sypd = np.append(sypd, value) # simulated years per day
    syph = 24./sypd # simulated year per hour

chpsy = syph*nptot # core-hours per simulated year
sbu = nptot*elapsed_time*470410408./(86400.*8098.*128.) # system billing units


# load balancing
file_name = 'load_balancing_info.txt'
file_paths = [sim_path + '/' + file_name for sim_path in simulation_paths]
tso = np.array([]); cto = np.array([]); wto = np.array([]) # ocean / NEMO
tsa = np.array([]); cta = np.array([]); wta = np.array([]) # atmos / OIFS
tsr = np.array([]); ctr = np.array([]); wtr = np.array([]) # runoff / RNFM
csync = np.array([])
for file_path in file_paths:
    label = 'oceanx simulation time'
    value = read_value_preceded_by_label(file_path, label)
    tso = np.append(tso, value)
    label = 'oceanx'
    value1, value2 = read_value_constrained_by_two_labels(file_path, label)
    cto = np.append(cto, value1)
    wto = np.append(wto, value2)
    label = 'OpenIFS simulation time'
    value = read_value_preceded_by_label(file_path, label)
    tsa = np.append(tsa, value)
    label = 'OpenIFS'
    value1, value2 = read_value_constrained_by_two_labels(file_path, label)
    cta = np.append(cta, value1)
    wta = np.append(wta, value2)
    label = 'RNFMAP simulation time'
    value = read_value_preceded_by_label(file_path, label)
    tsr = np.append(tsr, value)
    label = 'RNFMAP'
    value1, value2 = read_value_constrained_by_two_labels(file_path, label)
    ctr = np.append(ctr, value1)
    wtr = np.append(wtr, value2)
    label = 'node clocks synchronisation'
    value = read_value_below_a_label(file_path, label)
    csync = np.append(csync, value)

# sort vectors based on oifs/nemo fraction
vectors = [ nodes, nfrac, npa, npo, tsa, cta, wta, tso, cto, wto, tsr, ctr, wtr, sypd, syph, chpsy, elapsed_time, sbu ]
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
