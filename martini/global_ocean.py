#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a table with the time evolution of some global variables of the ocean 
with and without seasonal filter: ws/ns

Authors
Alessandro Sozza (CNR-ISAC, Oct 2023)
"""

import numpy as np
from sklearn.linear_model import LinearRegression
import xarray as xr
import os
import glob
import datetime
import subprocess
import shutil
import argparse
import matplotlib.pyplot as plt
from functions import preproc_nemo
from functions import dateDecimal
from functions import interp_average
from functions import moving_average

# the folder where the experiments are
RUNDIR="/ec/res4/scratch/itas/ece4"

def parse_args():
    """Command line parser for global ocean"""

    parser = argparse.ArgumentParser(description="Command Line Parser for global ocean analysis")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("startyear", metavar="STARTYEAR", help="Start of the Window (year)", type=str)
    parser.add_argument("endyear", metavar="ENDYEAR", help="End of the Window (year)", type=str)

    parsed = parser.parse_args()

    return parsed

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
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo)

    # dictionaries for mean quantities
    avews = {}  # with seasons - original
    avens = {}  # no seasons - moving average
    fieldnames = []

    avews['time'] = dateDecimal(data['time'].values)
    avens['time'] = dateDecimal(data['time'].values)
    timef = len(data['time'].values)
    fieldnames.append('time')

    # 3d fields
    for field in ['to', 'so']:
        avews[f'{field}g'] = data[f'{field}'].weighted(vol).mean(dim=['z', 'y', 'x']).values.flatten()
        fieldnames.append(f'{field}g')
        avews[f'{field}m'] = data[f'{field}'].isel(z=slice(0,23)).weighted(vol.isel(z=slice(0,23))).mean(dim=['z', 'y', 'x']).values.flatten()
        fieldnames.append(f'{field}m')
        avews[f'{field}p'] = data[f'{field}'].isel(z=slice(24,45)).weighted(vol.isel(z=slice(24,45))).mean(dim=['z', 'y', 'x']).values.flatten()
        fieldnames.append(f'{field}p')
        avews[f'{field}b'] = data[f'{field}'].isel(z=slice(46,74)).weighted(vol.isel(z=slice(46,74))).mean(dim=['z', 'y', 'x']).values.flatten()
        fieldnames.append(f'{field}b')

    # 2d fields
    for field in ['tos', 'sos', 'heatc', 'saltc', 'qsr_oce', 'qns_oce', 'qt_oce']: #, 'sfx', 'wfo']:
        avews[f'{field}g'] = data[f'{field}'].weighted(area).mean(dim=['y', 'x']).values.flatten()
        fieldnames.append(f'{field}g')

    # compute moving average to remove the seasonal component from all fields (expect time)
    for field in fieldnames[1:]:
        avens[f'{field}'] = moving_average(avews[f'{field}'], 12)

    ############################
    # write legend in file    
    row = "# "
    i = 1
    try:
        with open( os.path.join(dirs['tmp'], 'global_ocean_legend.dat'), 'w') as file: 
            for field in fieldnames:
                row += f'{field}('+f'{i}'+') '
                i += 1
            print(row, file=file)
    except FileExistsError:
        pass

    # write output
    for kind in ['ws', 'ns']:
        output = os.path.join('global_ocean_' + startyear + '-' + endyear + '_' + f'{kind}.dat')
        with open( os.path.join(dirs['tmp'], output), 'w') as file:
            for i in range(timef-1):
                if kind == 'ws':
                    row = [f"{avews[field][i]:<5}" for field in fieldnames]
                if kind == 'ns':
                    row = [f"{avens[field][i]:<5}" for field in fieldnames]
                print(" ".join(row), file=file)
