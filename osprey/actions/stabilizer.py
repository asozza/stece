#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stabilizer of water column

Author: Alessandro Sozza (CNR-ISAC) 
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