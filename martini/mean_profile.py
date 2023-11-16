#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate vertical profiles averaged over a time window

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
    """Command line parser for mean profile"""

    parser = argparse.ArgumentParser(description="Command Line Parser for mean profiles")

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
    profiles = {}  # with seasons - original
    fieldnames = []

    timef=data['time'].values
    zf = len(data['z'].values)
    profiles['z']=data['z'].values
    fieldnames.append('z')

    for field in ['to', 'so']:
        profiles[f'{field}f'] = data[f'{field}'].weighted(area).mean(dim=['time', 'y', 'x']).values.flatten()
        fieldnames.append(f'{field}')
    
    ############################
    # write legend in file    
    row = "# "
    i = 1
    try:
        with open( os.path.join(dirs['tmp'], 'mean_profile_legend.dat'), 'w') as file: 
            for field in fieldnames:
                row += f'{field}('+f'{i}'+') '
                i += 1
            print(row, file=file)
    except FileExistsError:
        pass

    # write output
    output = os.path.join('mean_profile_' + startyear + '-' + endyear + '.dat')
    with open( os.path.join(dirs['tmp'], output), 'w') as file:
        for i in range(zf-1):
            row = [f"{profiles[field][i]:<5}" for field in fieldnames]
            print(" ".join(row), file=file)
