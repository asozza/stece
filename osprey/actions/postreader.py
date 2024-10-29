#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Postreader module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: June 2024
"""

import os
import yaml
import logging
import numpy as np
import xarray as xr
import cftime
import dask

from osprey.utils.vardict import vardict
from osprey.utils.folders import folders, paths
from osprey.utils.time import get_leg, get_decimal_year
from osprey.utils.utils import error_handling_decorator
from osprey.means.means import globalmean, spacemean, timemean
from osprey.actions.reader import reader_nemo, reader_rebuilt, reader_nemo_field
from osprey.actions.rebuilder import rebuilder
from osprey.utils.utils import remove_existing_file
from osprey.means.means import apply_cost_function

# dask optimization of blocksizes
dask.config.set({'array.optimize_blockwise': True})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    filename = os.path.join(dirs['post'], f"{diagname}_{varlabel}_{metric}_{startyear}-{endyear}.nc")
    logger.info('File to be loaded %s', filename)
    data = xr.open_dataset(filename, use_cftime=True)
    
    return data

def writer_averaged(data, expname, startyear, endyear, varlabel, diagname, metric):
    """ 
    Writer of averaged data 
    
    Args:
    data: data array
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
    metric: tag indicating the type of cost function [base, diff, var, rel ...]
    
    """

    dirs = folders(expname)

    # Write averaged data on file
    os.makedirs(dirs['post'], exist_ok=True)
    filename = os.path.join(dirs['post'], f"{diagname}_{varlabel}_{metric}_{startyear}-{endyear}.nc")
    logger.info('File to be saved at %s', filename)
    data.to_netcdf(filename)

    return None

# MAIN FUNCTION
def postreader_nemo(expname, startyear, endyear, varlabel, diagname, orca='ORCA2', replace=False, metric='base', refinfo=None):
    """ 
    Postreader_nemo: main function for reading averaged data
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
    orca: ORCA configuration [ORCA2, eORCA1]
    replace: replace existing averaged file [False or True]
    metric: compute distance with respect to a reference field using a cost function
            all details provided in meanfield.yaml
    refinfo = {'expname': '****', 'startyear': ****, 'endyear': ****}

    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    dirs = folders(expname)
    info = vardict('nemo')[varname]

    # try to read averaged data
    try:
        if not replace:
            data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric=metric)
            logger.info('Averaged data found.')
            return data                
    except FileNotFoundError:
        logger.info('Averaged data not found. Creating new file ...')

    # try to read REF 'base' averaged data, otherwise read original data
    if metric != 'base':
        try:
            if not replace:
                xdata = reader_averaged(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varlabel=varlabel, diagname=diagname, metric='base')
                logger.info('Averaged base data found.')
        except FileNotFoundError:
            logger.info('Averaged base data not found. Creating new file ...')
            ds = reader_nemo_field(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varname=varname)
            xdata = averaging(data=ds, varlabel=varlabel, diagname=diagname, orca=orca)
            writer_averaged(data=xdata, expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varlabel=varlabel, diagname=diagname, metric='base')

    # try to read 'base' averaged data, otherwise read original data
    try:
        if not replace:
            data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric='base')
            logger.info('Averaged base data found.')
    except FileNotFoundError:
        logger.info('Averaged base data not found. Creating new file ...')
        ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
        data = averaging(data=ds, varlabel=varlabel, diagname=diagname, orca=orca)
        writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric='base')

    # apply cost function
    if metric != 'base':
        data = apply_cost_function(data, xdata, metric)
        writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric=metric)

    # Now you can read
    data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric=metric)
    
    return data


def averaging(data, varlabel, diagname, orca):
    """ 
    Averaging: Perform different flavours of averaging 
    
    Args:
    data: data array of a single field
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name <timeseries, profile, hovmoller, map, field, pdf>
    orca: ORCA configuration <ORCA2, eORCA1>
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = vardict('nemo')[varname]

    # timeseries
    if diagname  == 'timeseries':
        tvec = get_decimal_year(data['time'].values)
        vec = spacemean(data=data, ndim=info['dim'], ztag=ztag, orca=orca)
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                            attrs = {'units' : 'years', 'long_name' : 'time'}), 
            varlabel : xr.DataArray(data = vec, dims = ['time'], coords = {'time': tvec}, 
                            attrs  = {'units' : info['units'], 'long_name' : info['long_name']})},
            attrs = {'description': 'ECE4/NEMO averaged timeseries'})

    # vertical profile
    if diagname == 'profile' and info['dim'] == '3D':
        zvec = data['z'].values.flatten()
        vec = globalmean(data=data, ndim='2D')
        ds = xr.Dataset({
            'z': xr.DataArray(data = zvec, dims = ['z'], coords = {'z': zvec}, 
                                 attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varname : xr.DataArray(data = vec, dims = ['z'], coords = {'z': zvec}, 
                                   attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO averaged profile'})

    # hovmoller diagram
    if diagname == 'hovmoller' and info['dim'] == '3D':
        tvec = get_decimal_year(data['time'].values)
        zvec = data['z'].values.flatten()
        vec = spacemean(data=data, ndim='2D')
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                        attrs = {'units' : 'years', 'long_name' : 'time'}), 
            'z': xr.DataArray(data = zvec, dims = ['z'], coords = {'z': zvec}, 
                        attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varname : xr.DataArray(data = vec, dims = ['time', 'z'], coords = {'time': tvec, 'z': zvec},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Hovmoller diagram'})

    # 2D horizontal map 
    if diagname == 'map':
        if info['dim'] == '2D':
            vec = timemean(data=data)
        if info['dim'] == '3D':
            vec  = globalmean(data=data, ndim='1D')
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            varlabel : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Averaged map'})

    # 3D time-averaged spatial-only field 
    if diagname == 'field' and info['dim'] == '3D':
        vec = timemean(data=data)
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']},
                        attrs = {'units' : 'm', 'long_name' : 'depth'}),                             
            varlabel : xr.DataArray(data = vec, dims = ['z', 'y', 'x'], coords = {'z': data['z'], 'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Time-averaged field'})

    # 2D time-averaged spatial-only field
    if diagname == 'field' and info['dim'] == '2D':
        vec = timemean(data=data)
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            varlabel : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Time-averaged field'})
        
    # 3D field with monthly variability
    if diagname == 'monthly_field' and info['dim'] == '3D':
        vec = timemean(data=data)
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                                 attrs = {'units' : 'years', 'long_name' : 'time'}),
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                                attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                                attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']}, 
                              attrs = {'units' : 'm', 'long_name' : 'depth'}),                             
            varlabel : xr.DataArray(data = vec, dims = ['time', 'z', 'y', 'x'], 
                                    coords = {'time': data['time'], 'z': data['z'], 'y': data['y'], 'x': data['x']}, 
                                    attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Yearly-averaged monthly field'})

    # 2D field with monthly variability
    if diagname == 'monthly_field' and info['dim'] == '2D':
        vec = timemean(data=data[varname])
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                        attrs = {'units' : 'years', 'long_name' : 'time'}),
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                                 
            varlabel : xr.DataArray(data = vec, dims = ['z', 'y', 'x'], coords = {'z': data['z'], 'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Yearly-averaged monthly field'})

    return ds


##########################################################################################

# Reader of multiple restarts (rebuilt or not)
def reader_restart(expname, startyear, endyear):
    """ 
    reader_restart: reader of NEMO restart files in a range of legs 
    
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
