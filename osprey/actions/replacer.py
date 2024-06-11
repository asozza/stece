#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Replacer

Author: Alessandro Sozza (CNR-ISAC)
Date: Oct 2023
"""

import subprocess
import numpy as np
import os
import glob
import shutil
import yaml
import dask
import cftime
import nc_time_axis
import xarray as xr
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
import osprey_io as osi
import osprey_means as osm
import osprey_tools as ost
import osprey.actions.checks as osc
import osprey_eof as ose


def replacer(expname, leg):
    """ Function to replace modified restart files in the run folder """

    dirs = osi.folders(expname)

    # cleaning
    browser = ['restart*.nc']
    for basefile in browser:
        filelist = sorted(glob.glob(os.path.join(dirs['exp'], basefile)))
        for file in filelist:
            if os.path.isfile(file):
                print('Removing' + file)
                os.remove(file)

    # create new links
    browser = ['restart.nc', 'restart_ice.nc']
    for file in browser:
        rebfile = os.path.join(dirs['tmp'], str(leg).zfill(3), file)
        resfile = os.path.join(dirs['restart'], str(leg).zfill(3), file)
        shutil.copy(rebfile, resfile)
        newfile = os.path.join(dirs['exp'], file)
        print("Linking rebuilt NEMO restart", file)            
        os.symlink(resfile, newfile)
    
    return None

