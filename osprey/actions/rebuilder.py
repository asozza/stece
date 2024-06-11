#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rebuilder

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

import osprey_io as osi
import osprey_means as osm
import osprey_tools as ost
import osprey_eof as ose

def rebuilder(expname, leg):
    """ Function to rebuild NEMO restart """

    dirs = osi.folders(expname)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)

    rebuilder = os.path.join(dirs['rebuild'], "rebuild_nemo")
  
    for kind in ['restart', 'restart_ice']:
        print(' Processing ' + kind)
        flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + kind + '_????.nc'))
        tstep = ost.get_nemo_timestep(flist[0])

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            try:
                os.symlink(filename, destination_path)
            except FileExistsError:
                pass

        rebuild_command = [rebuilder, "-m", os.path.join(dirs['tmp'], str(leg).zfill(3), expname + "_" + tstep + "_" + kind ), str(len(flist))]
        try:
            subprocess.run(rebuild_command, stderr=subprocess.PIPE, text=True, check=True)
            for file in glob.glob('nam_rebuld_*') : 
                os.remove(file)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print(error_message) 

        for filename in flist:
            destination_path = os.path.join(dirs['tmp'], str(leg).zfill(3), os.path.basename(filename))
            os.remove(destination_path)

    # read timestep
    #filelist = glob.glob(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc'))    
    #timestep = ost.get_nemo_timestep(filelist[0])

    # copy restart
    #shutil.copy(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart.nc'), os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart.nc'))
    #shutil.copy(os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart_ice.nc'), os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart_ice.nc'))

    # remove 
    #os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart.nc'))
    #os.remove(os.path.join(dirs['tmp'], expname + '_' + timestep + '_restart_ice.nc'))

    flist = glob.glob('nam_rebuild*')
    for file in flist:
        os.remove(file)

    return None

