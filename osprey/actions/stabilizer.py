#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stabilizer of water column

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC) 
Date: Jun 2024
"""

import subprocess
import numpy as np
import os
import glob
import shutil
import yaml
import xarray as xr
import dask
import cftime
import nc_time_axis

def _eos(T, S, z):
    """ seawater equation of state """

    a0 = 1.6650e-1
    b0 = 7.6554e-1
    l1 = 5.9520e-2
    l2 = 5.4914e-4
    nu = 2.4341e-3
    m1 = 1.4970e-4
    m2 = 1.1090e-5
    R0 = 1026.0

    R = (-a0*(1.0+0.5*l1*(T-10.)+m1*z)*(T-10.)+b0*(1.0-0.5*l2*(S-35.)-m2*z)*(S-35.)-nu*(T-10.)*(S-35.))/R0

    return R

def stabilizer(nc_file):
    """ stabilizer of temperature and salinity profiles  """    

    # Open the NetCDF file
    ds = xr.open_dataset(nc_file)
    
    # Extract temperature and salinity fields
    temperature = ds['temperature']
    salinity = ds['salinity']
    
    # create density field using the state equation: alpha*T+beta*S?
    rho = temperature + salinity

    # Calculate the vertical derivative of temperature and salinity
    dTdz = temperature.diff('depth') / temperature['depth'].diff('depth')
    dSdz = salinity.diff('depth') / salinity['depth'].diff('depth')
    
    # Define a threshold for instability (this is an example, you may need to adjust it)
    instability_threshold = 0  # Example threshold, needs to be defined appropriately
    
    # Identify unstable zones
    unstable_zones = (dTdz > instability_threshold)

    # Correct unstable zones by homogenizing temperature
    for i in range(temperature.shape[0] - 1):
        unstable_layer = unstable_zones.isel(depth=i)
        if unstable_layer.any():
            # Calculate mean temperature for the unstable layer
            temp_mean = (temperature.isel(depth=i) + temperature.isel(depth=i + 1)) / 2
            
            # Apply the mean temperature to the unstable layer
            temperature[i:i+2] = temp_mean
    
    # Update the dataset with the corrected temperature
    ds['temperature'] = temperature
    
    # Save the modified dataset to a new NetCDF file
    ds.to_netcdf('corrected_' + nc_file)
    
    # Close the dataset
    ds.close()

    return None