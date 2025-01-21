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
import netCDF4 as nc

from osprey.utils import config
from osprey.utils.utils import get_nemo_timestep


def delete_attrs(file):
    # Open the dataset in 'r+' mode to allow modifications
    with nc.Dataset(file, 'r+') as dataset:
        # Iterate over all variables in the dataset
        for var_name, variable in dataset.variables.items():
            # Get all attribute names for the variable
            attr_names = list(variable.ncattrs())
            # Delete each attribute
            for attr in attr_names:
                variable.delncattr(attr)  # Correct method to delete an attribute

    return None


def writer_restart(expname, rdata, leg):
    """ Write NEMO restart file in a temporary folder """

    dirs = config.folders(expname)
    flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + 'restart' + '_????.nc'))
    timestep = get_nemo_timestep(flist[0])

    # ocean restart creation
    oceout = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart.nc')
    rdata.to_netcdf(oceout, mode='w', unlimited_dims={'time_counter': True})

    # delete attributes
    delete_attrs(oceout)

    # copy ice restart
    orig = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart_ice.nc')
    dest = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart_ice.nc')
    shutil.copy(orig, dest)

    return None



