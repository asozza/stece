#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Postreader module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: June 2024
"""

import os
import logging
import yaml
import numpy as np
import xarray as xr
import cftime
import dask

from osprey.utils import catalogue
from osprey.utils.folders import folders
from osprey.utils.time import get_leg
from osprey.utils.utils import error_handling_decorator
from osprey.utils.utils import remove_existing_file

from osprey.means.means import spacemean, timemean
from osprey.means.means import apply_cost_function

from osprey.actions.reader import reader_rebuilt, reader_nemo_field
from osprey.actions.rebuilder import rebuilder

# dask optimization of blocksizes
dask.config.set({'array.optimize_blockwise': True})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# dictionary of months by seasons
season_months = {"DJF": [12, 1, 2], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11]}

def _update_description(data, refinfo):

    description = data.attrs.get('description', 'No description')  # Recupera la descrizione esistente o usa un default
    if 'refinfo' in locals() and isinstance(refinfo, dict):  # Controlla se refinfo esiste
        refinfo_str = ', '.join([f"{key}: {value}" for key, value in refinfo.items()])
        description += f" {refinfo_str}"
    data.attrs['description'] = description

    return data

##########################################################################################
# Reader for averaged data

def reader_averaged(expname, startyear, endyear, varlabel, diagname, format, metric, refinfo):
    """ 
    Reader of averaged data 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [series, prof, hovm, map, fld, pdf]
    format: time format [plain, global, monthly, seasonally, yearly]
    metric: tag indicating the type of cost function [base, diff, var, rel, ...]
    
    """

    dirs = folders(expname)

    filename = f"{varlabel}_{expname}_{startyear}-{endyear}_{diagname}_{format}_{metric}"
    if metric != 'base':
        filename += f"_{refinfo['expname']}_{refinfo['startyear']}-{refinfo['endyear']}_{refinfo['diagname']}_{refinfo['format']}"
    filename = os.path.join(dirs['post'], f"{filename}.nc")

    logging.info('File to be loaded %s', filename)
    data = xr.open_dataset(filename, use_cftime=True)
    
    return data


def writer_averaged(data, expname, startyear, endyear, varlabel, diagname, format, metric, refinfo):
    """ 
    Writer of averaged data 
    
    Args:
    data: data array
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [series, prof, hovm, map, fld, pdf]
    format: time format [plain, global, monthly, seasonally, yearly]
    metric: tag indicating the type of cost function [base, diff, var, rel, ...]
    
    """

    dirs = folders(expname)
    filename = f"{varlabel}_{expname}_{startyear}-{endyear}_{diagname}_{format}_{metric}"
    if metric != 'base':
        filename += f"_{refinfo['expname']}_{refinfo['startyear']}-{refinfo['endyear']}_{refinfo['diagname']}_{refinfo['format']}"
    filename = os.path.join(dirs['post'], f"{filename}.nc")

    logging.info('File to be loaded %s', filename)
    data.to_netcdf(filename, mode='w', engine='netcdf4', format='NETCDF4')

    return None


# MAIN FUNCTION
def postreader_nemo(expname, startyear, endyear, varlabel, diagname, format='plain', orca='ORCA2', replace=False, metric='base', refinfo=None):
    """ 
    Postreader_nemo: main function for reading averaged data
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [series, prof, hovm, map, fld, pdf]
    format: time format [plain, global, monthly, seasonally, yearly]
    orca: ORCA configuration [ORCA2, eORCA1]
    replace: replace existing averaged file [False or True]
    metric: compute distance with respect to a reference field using a cost function
    refinfo = {'expname': '****', 'startyear': ****, 'endyear': ****, 'diagname': '*', 'format': '*'}
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    dirs = folders(expname)
    info = catalogue.observables('nemo')[varname]

    ## try to read averaged data
    try:
        if not replace:
            data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric, refinfo=refinfo)
            logging.info('Averaged data found.')
            return data 
        else:
            # When replace is True, skip checking for the file and recreate it
            raise FileNotFoundError  # Trigger the exception deliberately to skip reading of averaged file
    except FileNotFoundError:
        if replace:
            logging.info('Averaged data to be replaced. Creating new file ...')
        else:
            logging.info('Averaged data not found. Creating new file ...')

    ## otherwise read original data and perform averaging
    ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
    data = averaging(data=ds, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
    writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric='base', refinfo=None)

    if metric == 'base':
        return data
    else:
        ## if metric is not 'base', compute cost function
        # read reference data or create averaged field
        try:
            if not replace:
                mds = reader_averaged(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], 
                                      varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], metric='base', refinfo=None)
                logging.info('Averaged reference data found.')
            else:
                # When replace is True, skip checking for the file and recreate it
                raise FileNotFoundError  # Trigger the exception deliberately to skip reading of averaged file
        except FileNotFoundError:
            if replace:
                logging.info('Averaged reference data to be replaced. Creating new file ...')
            else:
                logging.info('Averaged reference data not found. Creating new file ...')
            xds = reader_nemo_field(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varname=varname)
            mds = averaging(data=xds, varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], orca=orca)
            writer_averaged(data=mds, expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], 
                            varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], metric='base', refinfo=None)

        # apply cost function
        if refinfo['diagname'] == 'field':

            # apply cost function first and averaging again afterwards
            data = apply_cost_function(data, mds, metric, format=format, format_ref=refinfo['format'])    
            data = averaging(data=data, varlabel=varlabel, diagname=diagname, format=format, orca=orca)

        else:

            # apply cost function to averaged data
            data = apply_cost_function(data, mds, metric, format=format, format_ref=refinfo['format'])               
            data = _update_description(data, refinfo)

        writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric, refinfo=refinfo)

    # Now you can read
    data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric, refinfo=refinfo)
    
    return data


def averaging(data, varlabel, diagname, format, orca):
    """ 
    Averaging: Perform different flavours of averaging 
    
    Args:
    data: data array of a single field
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [scalar, series, prof, hovm, map, fld, pdf]
    format: time format [plain, global, monthly, seasonally, yearly]
    orca: ORCA configuration <ORCA2, eORCA1>
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    info = catalogue.observables('nemo')[varname]
    #cinfo = catalogue.coordinates('nemo')

    # scalar / single-valued
    if diagname == 'scalar' or (diagname == 'timeseries' and format == 'global'):
        
        ds = timemean(data=data, format='global')
        ds = spacemean(data=ds, ndim=info['dim'], ztag=ztag, orca=orca)
        
        ds = xr.Dataset({
            varlabel : xr.DataArray(data = ds, dims = [], coords = {},
                            attrs  = {'units' : info['units'], 'long_name' : info['long_name']})},
            attrs = {'description': 'ECE4/NEMO global averaged scalar'})

    # timeseries
    if diagname == 'timeseries' and format != 'global':

        ds = timemean(data=data, format=format)
        ds = spacemean(data=ds, ndim=info['dim'], ztag=ztag, orca=orca)

        if format == 'yearly':
                dates = [cftime.DatetimeGregorian(year, 7, 1, 0, 0, 0, has_year_zero=False) for year in ds['year'].values]
                ds = xr.DataArray(data=ds, dims=["time"], coords={"time": dates})

        if format == 'monthly':
            last_year = data['time.year'].values[-1]
            dates = [cftime.DatetimeGregorian(last_year, month, 1, 0, 0, 0, has_year_zero=False) for month in range(1, 13)]
            ds = xr.DataArray(data=ds, dims=["time"], coords={"time": dates})

        if format == 'seasonally':
            last_year = data['time.year'].values[-1]
            dates = [cftime.DatetimeGregorian(last_year, month, 1, 0, 0, 0, has_year_zero=False) for month in range(1, 13)]
            values = []
            for month in range(1, 13):
                for season, months in season_months.items():
                    if month in months:
                        values.append(ds.sel(season=season).values)
                        break
            ds = xr.DataArray(data=values, dims=["time"], coords={"time": dates})

        ds = xr.Dataset({
                varlabel : xr.DataArray(data=ds, dims=[ds.dims[0]], coords={ds.dims[0]: ds['time']}, 
                                        attrs  = {'units': info['units'], 'long_name': info['long_name']})}, 
                attrs = {'description': 'ECE4/NEMO averaged timeseries'})

    # vertical profile
    if (diagname == 'profile' and info['dim'] == '3D'):
        
        zvec = data['z'].values.flatten()
        vec = timemean(data=data, format='global')
        vec = spacemean(data=vec, ndim='2D', ztag=ztag, orca=orca)

        ds = xr.Dataset({
            'z': xr.DataArray(data = zvec, dims = ['z'], coords = {'z': zvec}, 
                              attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varname : xr.DataArray(data = vec, dims = ['z'], coords = {'z': zvec}, 
                                   attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO averaged profile'})

    # hovmoller diagram
    if (diagname == 'hovmoller' and info['dim'] == '3D'):

        if format == 'plain':
            time_coord_name = 'time'
            tvec = data['time'].values  # Preserve as cftime       

        elif format == 'monthly':
            time_coord_name = 'month'
            tvec = data['time.month'].values[:12]

        elif format == 'seasonally':
            time_coord_name = 'season'
            tvec = data['time.season'].values[:4]

        elif format == 'yearly':
            time_coord_name = 'year'
            tvec = data['time.year'].values[::12]

        zvec = data['z'].values.flatten()
        vec = timemean(data=data, format=format)        
        vec = spacemean(data=vec, ndim=info['dim'], ztag=ztag, orca=orca)
        if format != 'plain' and 'time' in vec:
            vec = vec.drop_vars('time')
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                        attrs = {'units' : 'years', 'long_name' : 'time'}), 
            'z': xr.DataArray(data = zvec, dims = ['z'], coords = {'z': zvec}, 
                        attrs = {'units' : 'm', 'long_name' : 'depth'}), 
            varname : xr.DataArray(data = vec, dims = ['time', 'z'], coords = {'time': tvec, 'z': zvec},
                        attrs  = {'units' : info['units'], 'long_name' : info['long_name']})}, 
            attrs = {'description': 'ECE4/NEMO Hovmoller diagram'})

    # 2D horizontal map 
    # ISSUE: time dimension still exist, if format != 'global'
    # e se volessi una mappa solo di una stagione?
    if diagname == 'map':
        vec = timemean(data=data, format='global')
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

