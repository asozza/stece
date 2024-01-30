#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a table with the time evolution of some global variables of the ocean 
with and without seasonal filter (flags 'ws' and 'ns')

Authors
Alessandro Sozza (CNR-ISAC, Oct 2023)
"""

import numpy as np
import xarray as xr
import os
import glob
import time
import datetime
import subprocess
import shutil
import argparse
import matplotlib.pyplot as plt
import goat_tool as gt

start_time = time.time()

# the folder where the experiments are
RUNDIR="/ec/res4/scratch/itas/ece4"

def parse_args():
    """Command line parser for time series"""

    parser = argparse.ArgumentParser(description="Command Line Parser for time series")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("startyear", metavar="STARTYEAR", help="Start of the Window (year)", type=str)
    parser.add_argument("endyear", metavar="ENDYEAR", help="End of the Window (year)", type=str)

    parser.add_argument("--nave", action="store_true", help="Normal Average")
    parser.add_argument("--mave", action="store_true", help="Moving Average")

    parsed = parser.parse_args()

    return parsed


###########################################################################################
# MAIN PROGRAM
if __name__ == "__main__":

    # parser
    args = parse_args()
    expname = args.expname
    startyear = args.startyear
    endyear = args.endyear

    # define directories
    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'tmp':  os.path.join("/ec/res4/scratch/itas/martini", expname, "goat"),
    }

    os.makedirs(dirs['tmp'], exist_ok=True)

    # simulation path
    expdir=os.path.join('/ec/res4/scratch/itas/ece4/', expname, 'output', 'nemo')

    # compute weights for the integrals
    domain = xr.open_dataset(os.path.join(expdir, '..', '..', 'domain_cfg.nc'))
    vol = domain['e1t']*domain['e2t']*domain['e3t_0']
    area = domain['e1t']*domain['e2t']

    # load dataset
    filelist = []
    for year in range(int(startyear), int(endyear) + 1):
        pattern = os.path.join(expdir, f"{expname}_oce_1m_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    data = xr.open_mfdataset(filelist, preprocess=gt.preproc_nemo_T)


    ###########################################################################################
    # normal average - with seasons
    if args.nave:
        ave = {} 
        fieldnames = []
        ave['time'] = gt.dateDecimal(data['time'].values)
        timef = len(data['time'].values)
        fieldnames.append('time')

        # 3d fields
        for field in ['to', 'so']:
            ave[f'{field}g'] = data[f'{field}'].weighted(vol).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}g')
            ave[f'{field}m'] = data[f'{field}'].isel(z=slice(0,23)).weighted(vol.isel(z=slice(0,23))).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}m')
            ave[f'{field}p'] = data[f'{field}'].isel(z=slice(24,45)).weighted(vol.isel(z=slice(24,45))).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}p')
            ave[f'{field}b'] = data[f'{field}'].isel(z=slice(46,74)).weighted(vol.isel(z=slice(46,74))).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}b')

        # write output
        output = os.path.join('time_series_' + startyear + '-' + endyear + '_nave.dat')
        with open( os.path.join(dirs['tmp'], output), 'w') as file:
            for i in range(timef):
                row = [f"{ave[field][i]:<5}" for field in fieldnames]
                print(" ".join(row), file=file)


    ###########################################################################################
    # moving average
    if args.mave:

        aux = {}
        ave = {}  
        fieldnames = []
        aux['time'] = data.time
        ave['time'] = gt.dateDecimal(data['time'].values)
        timef = len(data['time'].values)
        fieldnames.append('time')

        # 3d fields
        for field in ['to', 'so']:
            aux[f'{field}g'] = data[f'{field}'].weighted(vol).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}g')
            aux[f'{field}m'] = data[f'{field}'].isel(z=slice(0,23)).weighted(vol.isel(z=slice(0,23))).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}m')
            aux[f'{field}p'] = data[f'{field}'].isel(z=slice(24,45)).weighted(vol.isel(z=slice(24,45))).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}p')
            aux[f'{field}b'] = data[f'{field}'].isel(z=slice(46,74)).weighted(vol.isel(z=slice(46,74))).mean(dim=['z', 'y', 'x']).values.flatten()
            fieldnames.append(f'{field}b')

        # compute moving average to remove the seasonal component from all fields (expect time)
        for field in fieldnames[1:]:
            ave[f'{field}'] = gt.moving_average(aux[f'{field}'], 12)

        # write output
        output = os.path.join('time_series_' + startyear + '-' + endyear + '_mave.dat')
        with open( os.path.join(dirs['tmp'], output), 'w') as file:
            for i in range(6,timef-6): # start from july | end in june
                row = [f"{ave[field][i]:<5}" for field in fieldnames]
                print(" ".join(row), file=file)


    ############################################################################
    # write legend in file    
    row = "# "
    i = 1
    try:
        with open( os.path.join(dirs['tmp'], 'time_series_legend.dat'), 'w') as file: 
            for field in fieldnames:
                row += f'{field}('+f'{i}'+') '
                i += 1
            print(row, file=file)
    except FileExistsError:
        pass

    # print computing time
    print("--- %s seconds ---" % (time.time() - start_time))