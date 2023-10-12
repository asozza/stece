#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
nemo-restart player
"""

import subprocess
import os
import glob
import shutil
import argparse
import xarray as xr

# on atos, you will need to have 
#export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/apps/netcdf4/4.9.1/INTEL/2021.4/lib:/usr/local/apps/hdf5/1.12.2/INTEL/2021.4/lib

def parse_args():
    """Command line parser for nemo-restart"""

    parser = argparse.ArgumentParser(description="Command Line Parser for nemo-restart")

    # add positional argument (mandatory)
    parser.add_argument("expname",  metavar="EXPNAME", help="experiment name")
    parser.add_argument("--rebuild", action="store_true", help="Enable nemo-rebuild")

    args = parser.parse_args()

    return args

def get_nemo_timestep(DIR, nemofilename):

    filelist = glob.glob(os.path.join(DIR, nemofilename))
    timestep = os.path.basename(filelist[0]).split('_')[1]

    return timestep

def rebuild_nemo(expname, REBUILD_DIR, TMP_DIR):

    EXP_DIR = os.path.join(BASE_DIR, expname)
    rebuilder = os.path.join(REBUILD_DIR, "rebuild_nemo")

    for kind in ['restart', 'restart_ice']: 
        print('Processing' + kind)
        #timestep = get_nemo_timestep(os.path.join(EXP_DIR, 'restart', '002'), expname + '*_' + kind + '_????.nc')
        filelist = glob.glob(os.path.join(EXP_DIR, 'restart', '002', expname + '*_' + kind + '_????.nc'))
        timestep = os.path.basename(filelist[0]).split('_')[1]

        for filename in filelist:
            destination_path = os.path.join(TMP_DIR, os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuilder, os.path.join(TMP_DIR,  expname + "_" + timestep + "_" + kind ), str(len(filelist))]
        try: 
            subprocess.run(rebuild_command, stderr=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print(error_message)     

        for filename in filelist:
            destination_path = os.path.join(TMP_DIR, os.path.basename(filename))
            os.remove(destination_path)


if __name__ == "__main__":
    
    # parser
    args = parse_args()

    BASE_DIR="/ec/res4/scratch/itas/ece4"
    TMP_DIR = "/lus/h2resw01/scratch/ccpd/martini"
    REBUILD_DIR="/ec/res4/scratch/itas/ece4/res1/restart/002"
    os.makedirs(TMP_DIR, exist_ok=True)

    expname = args.expname

    if args.rebuild:
        rebuild_nemo(expname=expname, REBUILD_DIR=REBUILD_DIR, TMP_DIR=TMP_DIR)

    timestep = get_nemo_timestep(TMP_DIR,  expname + '*_restart.nc')
    oce = os.path.join(TMP_DIR, expname + '_' + timestep + '_restart.nc')
    xfield = xr.open_dataset(oce)
    varlist = ['tn', 'tb']
    for var in varlist: 
        xfield[var] = xr.where(xfield[var]!=0, xfield[var] - 0.5, 0.)
    
    # ocean restart creation
    oceout = os.path.join(TMP_DIR, 'restart.nc')
    xfield.to_netcdf(oceout)

    # ice restaart copy
    shutil.copy(os.path.join(TMP_DIR, expname + '_' + timestep + '_restart_ice.nc'), os.path.join(TMP_DIR, 'restart_ice.nc'))










