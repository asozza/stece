#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Post-Reader module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: June 2024
"""

import os
import yaml
import logging
import numpy as np
import xarray as xr

from osprey.utils.vardict import vardict
from osprey.utils.folders import folders, paths
from osprey.utils.time import get_leg, get_decimal_year
from osprey.means.means import spacemean, timemean
from osprey.actions.reader import reader_nemo, reader_rebuilt
from osprey.actions.reader import elements
from osprey.actions.rebuilder import rebuilder
from osprey.utils.utils import remove_existing_file
from osprey.means.means import cost

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


##########################################################################################
# Reader for averaged data

def reader_averaged(expname, startyear, endyear, varlabel, diagname, metric):
    """ 
    Reader of averaged data 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
    metric: tag indicating the type of cost function [base, diff, var, rel ...]
    
    """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"{diagname}_{varlabel}_{metric}_{startyear}-{endyear}.nc")
    logger.info('File to be loaded %s', filename)
    data = xr.open_dataset(filename, use_cftime=True)

    return data

# MAIN FUNCTION
def postreader_averaged(expname, startyear, endyear, varlabel, diagname, replace=False, metric='base', orca='ORCA2'):
    """ 
    Post-reader Main 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
                            or [ts, prof, hovm, map, fld, pdf]?
    replace: replace existing averaged file [False or True]
    metric: compute distance with respect to a reference field using a metric (cost function)
             all details should be provided in the meanfield.yaml file
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    dirs = folders(expname)
    
    # try to read averaged data
    try:
        if replace == False:
            data = reader_averaged(expname, startyear, endyear, varlabel, diagname, metric)
            logger.info('Averaged data found.')        
            return data
    except FileNotFoundError:
        logger.info('Averaged data not found. Creating new file ...')

    # If averaged data not existing, read original data
    xdata = reader_nemo(expname, startyear, endyear)

    # If anomaly is True
    if metric != 'base':
        # read from yaml file
        local_paths = paths()
        filename = os.path.join(local_paths['osprey'], 'meanfield.yaml')
        with open(filename) as yamlfile:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)    
        if 'meanfield' in config:
            meanfield = config['meanfield']
            exp0 = meanfield[0]['expname']
            y0 = meanfield[1]['startyear']
            y1 = meanfield[2]['endyear']
        mdata = reader_averaged(expname=exp0, startyear=y0, endyear=y1, varlabel=varlabel, diagname='field', metric='base')
        xdata = cost(xdata, mdata, metric)

    ds = averaging(expname, xdata, varlabel, diagname)

    # Write averaged data on file
    os.makedirs(dirs['perm'], exist_ok=True)
    filename = os.path.join(dirs['perm'], f"{diagname}_{varlabel}_{metric}_{startyear}-{endyear}.nc")
    if replace == True:
        remove_existing_file(filename)
    logger.info('File to be saved at %s', filename)
    ds.to_netcdf(filename)

    # Now you can read
    data = reader_averaged(expname, startyear, endyear, varlabel, diagname, metric)

    return data


def averaging(expname, data, varlabel, diagname, orca='ORCA2'):
    """ 
    Averaging: Perform different flavours of averaging 
    
    Args:
    expname: experiment name
    data: dataset
    varlabel: variable label
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    df = elements(orca)
    info = vardict('nemo')[varname]

    # timeseries (why not saving in cftime?)
    if diagname  == 'timeseries':
        tvec = get_decimal_year(data['time'].values)
        vec = spacemean(data, varname, info['dim'], ztag)
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                            attrs = {'units' : 'years', 'long_name' : 'years'}), 
            varlabel : xr.DataArray(data = vec, dims = ['time'], coords = {'time': tvec}, 
                            attrs  = {'units' : info['units'], 'long_name' : info['long_name']})},
            attrs = {'description': 'ECE4/NEMO averaged timeseries data'})

    # vertical profile
    if diagname == 'profile' and info['dim'] == '3D':
        zvec = data['z'].values.flatten()
        vec = data[varname].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
        ds = xr.Dataset({
            'z': xr.DataArray(data = zvec, dims = ['z'], coords = {'z': zvec}, 
                                 attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varname : xr.DataArray(data = vec, dims = ['z'], coords = {'z': zvec}, 
                                   attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO averaged profiles'})

    # hovmoller diagram
    if diagname == 'hovmoller' and info['dim'] == '3D':
        tvec = get_decimal_year(data['time'].values)
        vec = spacemean(data, varname, '2D')
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                        attrs = {'units' : 'years', 'long_name' : 'years'}), 
            'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']}, 
                        attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varlabel : xr.DataArray(data = vec, dims = ['time', 'z'], coords = {'time': tvec, 'z': data['z']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO averaged hovmoller diagram'})

    # map
    if diagname == 'map':
        if info['dim'] == '2D':
            vec = timemean(data, varname)
        if info['dim'] == '3D':
            vec  = spacemean(data, varname, info['dim'])
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            varlabel : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO averaged map'})

    # field
    if diagname == 'field' and info['dim'] == '3D':
        vec = timemean(data, varname)
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']},
                        attrs = {'units' : 'm', 'long_name' : 'depth'}),                             
            varlabel : xr.DataArray(data = vec, dims = ['z', 'y', 'x'], coords = {'z': data['z'], 'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO time-averaged field'})

    if diagname == 'field' and info['dim'] == '2D':
        vec = timemean(data, varname)
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            varlabel : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO time-averaged field'})

    return ds

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