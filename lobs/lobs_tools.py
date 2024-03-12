#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 _       _         _
| |     | |  ___ _| |_  ___  _
| | ___ | |_/ __|_   _|/ _ \| |__
| |/ _ \| _ \__ \ | |_|  __/|  _/
|_|\___/|___/___/ |____\___\|_|

LOBSTER: Load balancing script for ec-earth4
--------------------------------------------
Functions and tools

Authors
Alessandro Sozza (CNR-ISAC, Mar 2024)
"""

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
        print(file_path," not found")
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
        print(file_path," not found")
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
        print(file_path," not found")
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
        print(file_path," not found")
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
# i/o operations, folders and legs
    
def mainpath():

    # read from yaml file
    with open('paths.yaml') as jf:
        config = yaml.load(jf, Loader=yaml.FullLoader)
    if 'folders' in config:
        folders = config['folders']
    for ifo in folders:
        path = ifo.get('path', '')

    return path

def folders(expname):

    path = mainpath()
    dirs = {
        'exp': os.path.join(path, expname),
        'log': os.path.join(path, expname, "log"),
    }

    return dirs

# extract final leg
def endleg(expname):

    dirs = folders(expname)
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)
    legs = leginfo['base.context']['experiment']['schedule']['leg']['num']

    return legs

#############################################################
# read single variables

def compute_nodes(expname):

    init=1
    dirs = folders(expname)
    path = os.path.join(dirs['log'], str(init).zfill(3), 'NODE.001_01')
    npa = read_value_preceded_by_label(path, 'NPROC') # nprocs of oifs, npa    
    path = os.path.join(dirs['log'], str(init).zfill(3), 'ocean.output')
    npo = read_value_preceded_by_label(path, 'jpnij') # nprocs of nemo, npo

    return npa,npo

def compute_sypd(expname, legs):

    dirs = folders(expname)    
    sypd = np.array([])
    for leg in range(1,int(legs)):
        path = os.path.join(dirs['log'], str(leg).zfill(3), 'timing.log')
        value = read_value_followed_by_label(path, 'SYPD') # simulated year per day, sypd
        sypd = np.append(sypd, value)
    
    return sypd

def compute_syph(expname, legs):

    dirs = folders(expname)
    syph = np.array([])
    for leg in range(1,int(legs)):
        path = os.path.join(dirs['log'], str(leg).zfill(3), 'timing.log')
        value = read_value_followed_by_label(path, 'SYPD') # simulated year per day, sypd
        syph = np.append(syph, 24./value)
    
    return syph

def compute_chpsy(expname, legs):

    init=1
    dirs = folders(expname)
    path = os.path.join(dirs['log'], str(init).zfill(3), 'NODE.001_01')
    npa = read_value_preceded_by_label(path, 'NPROC') # nprocs of oifs, npa    
    path = os.path.join(dirs['log'], str(init).zfill(3), 'ocean.ouput')
    npo = read_value_preceded_by_label(path, 'jpnij') # nprocs of nemo, npo
    nptot = npo+npa+1 # total nprocs

    chpsy = np.array([])
    for leg in range(1,int(legs)):
        path = os.path.join(dirs['log'], str(leg).zfill(3), 'timing.log')
        value = read_value_followed_by_label(path, 'SYPD') # simulated year per day, sypd
        chpsy = np.append(chpsy, 24.*nptot/value)
    
    return chpsy

def compute_elapsedtime(expname, legs):

    dirs = folders(expname)
    elapsedtime = np.array([])
    for leg in range(1,int(legs)):
        path = os.path.join(dirs['log'], str(leg).zfill(3), 'timing.log')
        hours, minutes, seconds = read_time_preceded_by_label(path, 'elapsed time')    
        value = hours*3600.+minutes*60.+seconds
        elapsedtime = np.append(elapsedtime, value)

    return elapsedtime

def compute_sbu(expname, legs):

    dirs = folders(expname)
    path = os.path.join(dirs['log'], str(legs).zfill(3), 'NODE.001_01')
    npa = read_value_preceded_by_label(path, 'NPROC') # nprocs of oifs, npa    
    path = os.path.join(dirs['log'], str(legs).zfill(3), 'ocean.ouput')
    npo = read_value_preceded_by_label(path, 'jpnij') # nprocs of nemo, npo
    nptot = npo+npa+1 # total nprocs

    sbu = np.array([])
    for leg in range(1,int(legs)):
        path = os.path.join(dirs['log'], str(leg).zfill(3), 'timing.log')
        hours, minutes, seconds = read_time_preceded_by_label(path, 'elapsed time')    
        time = hours*3600.+minutes*60.+seconds
        value = nptot*time*470410408./(86400.*8098.*128.) # system billing units, sbu
        sbu = np.append(sbu, value)

    return sbu

#############################################################
# collect variables from multiple runs
def group_by_nptot_sypd(expnames, leg):
    
    npo = np.array([])
    npa = np.array([])
    for expname in expnames:
        np1,np2 = compute_nodes(expname)
        npa = np.append(npa, np1)
        npo = np.append(npo, np2)    
    nptot = npo+npa+1

    ave=np.array([])
    for expname in expnames:
        if leg == 0:
            legs = endleg(expname)
        else:
            legs = leg
        sypd = compute_sypd(expname, legs)
        ave = np.append(ave,np.mean(sypd))

    return nptot,ave

#############################################################
# plots

def plot_sypd_vs_time(expname, leg):

    if leg == 0:
        legs = endleg(expname)
    else:
        legs = leg
    sypd = compute_sypd(expname, legs)
    x = [leg for leg in range(1,legs)]
    plt.xlabel("leg")
    plt.ylabel("SYPD")
    pp = plt.plot(x,sypd)

    return pp

def plot_sypd_vs_nptot(expnames, leg):

    nptot,sypd = group_by_nptot_sypd(expnames, leg)
    plt.xlabel("NPTOT")
    plt.ylabel("SYPD")
    pp = plt.scatter(nptot,sypd)
    pp = plt.plot(nptot,sypd)
    
    return pp

# multiplots
#  missing: averages and plots vs nptot e nfrac (for different expnames)
#  create plot at fixed number of nodes, ordered by nfrac
###############################################################

