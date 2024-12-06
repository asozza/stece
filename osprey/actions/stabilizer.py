#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stabilizer of water column

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC) 
Date: Jun 2024
"""

import numpy as np
import xarray as xr
import dask
import gsw


def stabilizer(data):
    """ stabilizer of potential density field  """    
    
    # Extract temperature and salinity fields
    z = data['z']
    lat = data['lat']
    pressure = gsw.p_from_z(-z, lat)
    temperature = data['thetao']
    salinity = data['so']
    
    # create density field using the state equation
    rho = gsw.density.rho(salinity, temperature, pressure)

    # Compute density gradient (dz is the vertical difference in depth)
    dz = data['z'].diff(dim='z')
    grad_rho = rho.diff(dim='z') / dz
    
    # Find unstable zones (density should increase with depth)
    unstable_zones = grad_rho.where(grad_rho < 0, drop=True)
    
    # If unstable zones exist, homogenize
    if not unstable_zones.isnull().all():
        for idx in unstable_zones.z:
            idx_next = idx + 1
            # Homogenize salinity and temperature between unstable layers
            salinity.loc[dict(z=slice(idx, idx_next))] = salinity.sel(z=slice(idx, idx_next)).mean(dim='z')
            temperature.loc[dict(z=slice(idx, idx_next))] = temperature.sel(z=slice(idx, idx_next)).mean(dim='z')
    
    data['thetao'] = temperature
    data['so'] = salinity
    
    return data


def constraints_for_restart(data):
    """ 
    Check and apply constraints to variables 
    
    U < 10 m/s, |ssh| < 20 m, S in [0,100] psu, T > -2.5 degC
    """ 

    # for horizontal velocity (u,v)
    for var in ['un', 'ub', 'vn', 'vb']:
        if var in data:
            data[var] = xr.where(data[var] > 10, 10, data[var])  # Ensure U < 10 m/s
    
    # for sea surface height (ssh)
    for var in ['sshn', 'sshb']:
        if var in data:
            data[var] = xr.where(np.abs(data[var]) > 20, 20 * np.sign(data[var]), data[var])  # Ensure |ssh| < 20
    
    # for salinity
    for var in ['sn', 'sb']:
        if var in data:
            data[var] = data[var].clip(0, 100)  # Ensure S in [0, 100]
    
    # for temperature
    for var in ['tn', 'tb']:
        if var in data:
            data[var] = xr.where(data[var] < -2.5, -2.5, data[var])  # Ensure T > -2.5

    return data

def constraints_for_fields(data):
    """ 
    Check and apply constraints to variables 
    
    U < 10 m/s, |ssh| < 20 m, S in [0,100] psu, T > -2.5 degC
    """ 

    # for horizontal velocity (u,v)
    for var in ['uo', 'vo']:
        if var in data:
            data[var] = xr.where(data[var] > 10, 10, data[var])  # Ensure U < 10 m/s
    
    # for sea surface height (ssh)
    for var in ['zos']:
        if var in data:
            data[var] = xr.where(np.abs(data[var]) > 20, 20 * np.sign(data[var]), data[var])  # Ensure |ssh| < 20
    
    # for salinity
    for var in ['so']:
        if var in data:
            data[var] = data[var].clip(0, 100)  # Ensure S in [0, 100]
    
    # for temperature
    for var in ['thetao']:
        if var in data:
            data[var] = xr.where(data[var] < -2.5, -2.5, data[var])  # Ensure T > -2.5

    return data