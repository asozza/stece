#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Post-Reader module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: June 2024
"""

import os
import logging
import numpy as np
import xarray as xr

from osprey.utils.vardict import vardict
from osprey.utils.folders import folders
from osprey.utils.time import get_leg, get_decimal_year
from osprey.means.means import spacemean, timemean
from osprey.actions.reader import reader_nemo, reader_rebuilt
from osprey.actions.reader import elements
from osprey.actions.rebuilder import rebuilder

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

##########################################################################################
# Reader of multiple restarts (rebuilt or not)

def reader_restart(expname, startyear, endyear):
    """ 
    Reader of NEMO restart files in a range of legs 
    
    Args:
    expname: experiment name
    startyear,endyear: time window

    """

    startleg = get_leg(startyear)
    endleg = get_leg(endyear)

    try:
        data = reader_rebuilt(expname, startleg, endleg)
        return data
    except FileNotFoundError:
        print(" Restart file not found. Rebuilding ... ")

    # rebuild files
    for leg in range(startleg,endleg+1):
        rebuilder(expname, leg)

    data = reader_rebuilt(expname, startleg, endleg)

    return data

##########################################################################################
# Reader for averaged data

def reader_averaged(expname, startyear, endyear, varname, diagname):
    """ 
    Reader of averaged data 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varname: variable name
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
          with prefixes [a: for anomaly]
    
    """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"{diagname}_{varname}_{startyear}-{endyear}.nc")
    logging.info(' File to be loaded %s', filename)
    data = xr.open_dataset(filename, use_cftime=True)

    return data

# MAIN FUNCTION
def postreader_averaged(expname, startyear, endyear, varname, diagname, replace=False):
    """ 
    Post-reader Main 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varname: variable name
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
              with prefixes [a: for anomaly]
    replace: replace existing averaged file [False or True]
          
    """

    dirs = folders(expname)
    df = elements(expname)
    ndim = vardict('nemo')[varname]

    # try to read averaged data
    try:
        data = reader_averaged(expname, startyear, endyear, varname, diagname)
        logging.info(' Averaged data found ')
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        logging.info('Averaged data not found. Creating new file ...')

    # If averaged data not existing, read original data
    data = reader_nemo(expname, startyear, endyear)

    ds = averaging(expname, data, varname, diagname)

    # Write averaged data on file
    os.makedirs(dirs['perm'], exist_ok=True)
    filename = os.path.join(dirs['perm'], f"{diagname}_{varname}_{startyear}-{endyear}.nc")
    logging.info(' File to be saved at %s', filename)
    ds.to_netcdf(filename)

    # Now you can read
    data = reader_averaged(expname, startyear, endyear, varname, diagname)

    return data


def averaging(expname, data, varname, diagname):
    """ 
    Averaging: Perform different flavours of averaging 
    
    Args:
    expname: experiment name
    data: dataset
    varname: variable name
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
          with prefixes [a: for anomaly]
    
    """

    df = elements(expname)
    ndim = vardict('nemo')[varname]

    # timeseries (why not saving in cftime?)
    if diagname  == 'timeseries':
        tvec = get_decimal_year(data['time'].values)
        vec = spacemean(data, varname, ndim)
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                            attrs = {'units' : 'years', 'long_name' : 'years'}), 
            varname : xr.DataArray(data = vec, dims = ['time'], coords = {'time': tvec}, 
                            attrs  = {'units' : data[varname].units, 'long_name' : data[varname].long_name})},
            attrs = {'description': 'ECE4/NEMO averaged timeseries data'})

    # vertical profile
    if diagname == 'profile' and ndim == '3D':
        zvec = data['z'].values.flatten()
        vec = data[varname].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
        ds = xr.Dataset({
            'z': xr.DataArray(data = zvec, dims = ['z'], coords = {'z': zvec}, 
                                 attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varname : xr.DataArray(data = vec, dims = ['z'], coords = {'z': zvec}, 
                                   attrs  = {'units' : data[varname].units, 'long_name' : data[varname].long_name})}, 
            attrs = {'description': 'ECE4/NEMO averaged profiles'})

    # hovmoller diagram
    if diagname == 'hovmoller' and ndim == '3D':
        tvec = get_decimal_year(data['time'].values)
        vec = spacemean(data, varname, '2D')
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                        attrs = {'units' : 'years', 'long_name' : 'years'}), 
            'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']}, 
                        attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varname : xr.DataArray(data = vec, dims = ['time', 'z'], coords = {'time': tvec, 'z': data['z']},
                        attrs  = {'units' : data[varname].units, 'long_name' : data[varname].long_name})}, 
            attrs = {'description': 'ECE4/NEMO averaged hovmoller diagram'})

    # map
    if diagname == 'map':
        if ndim == '2D':
            vec = timemean(data, varname)
        if ndim == '3D':
            vec  = spacemean(data, varname, ndim)
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            varname : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : data[varname].units, 'long_name' : data[varname].long_name})}, 
            attrs = {'description': 'ECE4/NEMO averaged map'})

    # field
    if diagname == 'field' and ndim == '3D':
        vec = timemean(data, varname)
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']},
                        attrs = {'units' : 'm', 'long_name' : 'depth'}),                             
            varname : xr.DataArray(data = vec, dims = ['z', 'y', 'x'], coords = {'z': data['z'], 'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : data[varname].units, 'long_name' : data[varname].long_name})}, 
            attrs = {'description': 'ECE4/NEMO time-averaged field'})

    if diagname == 'field' and ndim == '2D':
        vec = timemean(data, varname)
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            varname : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : data[varname].units, 'long_name' : data[varname].long_name})}, 
            attrs = {'description': 'ECE4/NEMO time-averaged field'})

    return ds

##########################################################################################

