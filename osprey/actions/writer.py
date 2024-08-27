#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Writer

Authors: Paolo Davini, Alessandro Sozza (CNR-ISAC)
Date: June 2024
"""

import os
import glob
import shutil

from osprey.utils.folders import folders
from osprey.utils.utils import get_nemo_timestep


def writer_restart(expname, rdata, leg):
    """ Write NEMO restart file in a temporary folder """

    dirs = folders(expname)
    flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + 'restart' + '_????.nc'))
    timestep = get_nemo_timestep(flist[0])

    # ocean restart creation
    oceout = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart.nc')
    rdata.to_netcdf(oceout, mode='w', unlimited_dims={'time_counter': True})

    # copy ice restart
    orig = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart_ice.nc')
    dest = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart_ice.nc')
    shutil.copy(orig, dest)

    return None



