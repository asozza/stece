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
from osprey.utils.folders import folders
from osprey.utils.time import get_leg, get_decimal_year
from osprey.utils.utils import error_handling_decorator
from osprey.utils.utils import remove_existing_file

from osprey.means.means import globalmean, spacemean, timemean
from osprey.means.means import apply_cost_function

from osprey.actions.reader import reader_rebuilt, reader_nemo_field
from osprey.actions.rebuilder import rebuilder

# dask optimization of blocksizes
dask.config.set({'array.optimize_blockwise': True})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


##########################################################################################
# Reader for averaged data

def reader_averaged(expname, startyear, endyear, varlabel, diagname, format, metric):
    """ 
    Reader of averaged data 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf]
    format: time format [plain, global, annual, monthly, seasonal]
    metric: tag indicating the type of cost function [base, diff, var, rel, ...]
    
    """

    dirs = folders(expname)
    filename = os.path.join(dirs['post'], f"{diagname}-{format}_{varlabel}_{metric}_{startyear}-{endyear}.nc")
    logging.info('File to be loaded %s', filename)
    data = xr.open_dataset(filename, use_cftime=True)
    
    return data

def writer_averaged(data, expname, startyear, endyear, varlabel, diagname, format, metric):
    """ 
    Writer of averaged data 
    
    Args:
    data: data array
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf]
    format: time format [plain, global, annual, monthly, seasonal]
    metric: tag indicating the type of cost function [base, diff, var, rel, ...]
    
    """

    dirs = folders(expname)
    os.makedirs(dirs['post'], exist_ok=True)
    filename = os.path.join(dirs['post'], f"{diagname}-{format}_{varlabel}_{metric}_{startyear}-{endyear}.nc")
    logging.info('File to be saved at %s', filename)
    data.to_netcdf(filename, mode='w')

    return None

# MAIN FUNCTION
def postreader_nemo(expname, startyear, endyear, varlabel, diagname, format='plain', orca='ORCA2', replace=False, metric='base', refinfo=None):
    """ 
    Postreader_nemo: main function for reading averaged data
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [scalar, timeseries, profile, hovmoller, map, field, pdf]
    format: time format [plain, global, annual, monthly, seasonally]
    orca: ORCA configuration [ORCA2, eORCA1]
    replace: replace existing averaged file [False or True]
    metric: compute distance with respect to a reference field using a cost function
            all details provided in meanfield.yaml
    refinfo = {'expname': '****', 'startyear': ****, 'endyear': ****, 'diagname': '*', 'format': '*'}
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    dirs = folders(expname)
    info = vardict('nemo')[varname]

    ## try to read averaged data
    try:
        if not replace:
            data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric)
            logging.info('Averaged data in metric "base" found.')
            return data 
    except FileNotFoundError:
        logging.info('Averaged data in metric "base" not found. Creating new file ...')

    ## otherwise read original data and perform averaging
    if metric == 'base':

        # if metric is 'base'
        ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
        data = averaging(data=ds, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
        writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric='base')
        return data

    else:

        ## if metric is not 'base', compute cost function
        # read reference data or create averaged field
        try:
            if not replace:
                mds = reader_averaged(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], 
                                      varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], metric='base')
                logging.info('Averaged reference data found.')
            else:
                # When replace is True, skip checking for the file and recreate it
                raise FileNotFoundError  # Trigger the exception deliberately to skip file reading
        except FileNotFoundError:
            logging.info('Averaged reference data not found or replace is True. Creating new file ...')
            xds = reader_nemo_field(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varname=varname)
            mds = averaging(data=xds, varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], orca=orca)
            writer_averaged(data=mds, expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], 
                            varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], metric='base')

        # apply cost function
        ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
        data = apply_cost_function(ds, mds, metric, format=refinfo['format'])
        if refinfo['diagname'] == 'field':
            data = averaging(data=data, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
        writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric)

    # Now you can read
    data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric)
    
    return data


def averaging(data, varlabel, diagname, format, orca):
    """ 
    Averaging: Perform different flavours of averaging 
    
    Args:
    data: data array of a single field
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [global, timeseries, profile, hovmoller, map, field, pdf]
    format: time format [plain, annual, monthly, seasonal]
    orca: ORCA configuration <ORCA2, eORCA1>
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = vardict('nemo')[varname]

    # scalar / single-valued
    if diagname == 'scalar' or (diagname == 'timeseries' and format == 'global'):
        vec = timemean(data=data, format='global')
        vec = spacemean(data=vec, ndim=info['dim'], ztag=ztag, orca=orca)
        ds = xr.Dataset({
            varlabel : xr.DataArray(data = vec, dims = [], coords = {},
                            attrs  = {'units' : info['units'], 'long_name' : info['long_name']})},
            attrs = {'description': 'ECE4/NEMO global averaged scalar'})

    # timeseries
    if diagname  == 'timeseries':
        tvec = get_decimal_year(data['time'].values)
        vec = timemean(data=data, format=format)        
        vec = spacemean(data=vec, ndim=info['dim'], ztag=ztag, orca=orca)
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = [vec.dims[0]], coords = {vec.dims[0]: tvec}, 
                            attrs = {'units' : vec.dims[0], 'long_name' : vec.dims[0]}), 
            varlabel : xr.DataArray(data = vec, dims = [vec.dims[0]], coords = {vec.dims[0]: tvec}, 
                            attrs  = {'units' : info['units'], 'long_name' : info['long_name']})},
            attrs = {'description': 'ECE4/NEMO averaged timeseries'})

    # vertical profile
    if diagname == 'profile' and info['dim'] == '3D':
        zvec = data['z'].values.flatten()
        vec = timemean(data=data, format=format)
        vec = spacemean(data=vec, ndim='2D', ztag=ztag, orca=orca)
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
        vec = timemean(data=data, format=format)        
        vec = spacemean(data=vec, ndim='2D', ztag=ztag, orca=orca)
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
        vec = timemean(data=data, format=format)
        if info['dim'] == '3D':
            vec  = spacemean(data=vec, ndim='1D', ztag=ztag, orca=orca)
        
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            varlabel : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Averaged map'})

    # time-averaged spatial-only field 
    if diagname == 'field':
        vec = timemean(data=data, format=format)

        data_vars = {
            'lat': xr.DataArray(data=data['lat'], dims=['y', 'x'], coords={'y': data['y'], 'x': data['x']}, 
                        attrs={'units': 'deg', 'long_name': 'latitude'}),
            'lon': xr.DataArray(data=data['lon'], dims=['y', 'x'], coords={'y': data['y'], 'x': data['x']}, 
                        attrs={'units': 'deg', 'long_name': 'longitude'})}

        if info['dim'] == '3D':
            data_vars['z'] = xr.DataArray(data=data['z'], dims=['z'], coords={'z': data['z']}, 
                        attrs={'units': 'm', 'long_name': 'depth'})
            data_vars[varlabel] = xr.DataArray(data=vec, dims=['z', 'y', 'x'], coords={'z': data['z'], 'y': data['y'], 'x': data['x']},
                        attrs={'units': info['units'], 'long_name': info['long_name']})
        elif info['dim'] == '2D': 
            data_vars[varlabel] = xr.DataArray(data=vec, dims=['y', 'x'], coords={'y': data['y'], 'x': data['x']},
                        attrs={'units': info['units'], 'long_name': info['long_name']})

        # Create the dataset
        ds = xr.Dataset(data_vars=data_vars, attrs={'description': 'ECE4/NEMO Time-averaged field'})


    # 3D field with monthly variability
    if diagname == 'field_monthly' and info['dim'] == '3D':
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
    if diagname == 'field_monthly' and info['dim'] == '2D':
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

