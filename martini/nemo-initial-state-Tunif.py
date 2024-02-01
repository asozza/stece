#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
modfy the NEMO T field files

Authors
Alessandro Sozza (CNR-ISAC, Dec 2023)
"""

import subprocess
import os
import glob
import shutil
import yaml
import argparse
import xarray as xr
from functions import preproc_nemo_T
from functions import moving_average
from functions import dateDecimal

# on atos, you will need to have
# module load intel/2021.4.0 intel-mkl/19.0.5 prgenv/intel hdf5 netcdf4 
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/apps/netcdf4/4.9.1/INTEL/2021.4/lib:/usr/local/apps/hdf5/1.12.2/INTEL/2021.4/lib

def parse_args():
    """Command line parser for nemo-restart"""

    parser = argparse.ArgumentParser(description="Command Line Parser for nemo-restart")

    # add positional argument (mandatory)
    parser.add_argument("expname", metavar="EXPNAME", help="Experiment name")
    parser.add_argument("year", metavar="YEAR", help="The years you want to process for rebuilding", type=str)
    parser.add_argument("temp", metavar="TEMP", help="New temp to be applied uniformly", type=float)
    parser.add_argument("salt", metavar="SALT", help="New salinity to be applied uniformly", type=float)

    parsed = parser.parse_args()

    return parsed


if __name__ == "__main__":
    
    # parser
    args = parse_args()
    expname = args.expname
    year = args.year
    temp = args.temp
    salt = args.salt

    # define directories
    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join("/ec/res4/scratch/itas/ece4/", expname, "output", "nemo"),
        'tmp':  os.path.join("/ec/res4/scratch/itas/martini", expname),
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo"
    }

    os.makedirs(dirs['tmp'], exist_ok=True)

    # load data
    filelist = os.path.join(dirs['nemo'], f"{expname}_oce_1y_T_{year}-{year}.nc")
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_T)

    # modify data
    data['thetao'] = xr.where(data['thetao']!=0, temp, 0.0)
    data['so'] = xr.where(data['so']!=0, salt, 0.0)

    # write output
    oceout = os.path.join(dirs['tmp'], f"initial-state_1y_T_{year}-{year}.nc")
    data.to_netcdf(oceout)

