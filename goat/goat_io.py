#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GOAT: Global Ocean & Atmosphere Trends
------------------------------------------------------
GOAT library for i/o operations

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import subprocess
import os
import glob
import yaml
import dask
import cftime
import netCDF4
import numpy as np
import xarray as xr
import goat_means as gm
import goat_tools as gt

def folders(expname): 
    
    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join("/ec/res4/scratch/itas/ece4/", expname, "output", "nemo"),
        'perm': os.path.join("/perm/itas/ece4", expname, "nemo")
    }

    os.makedirs(dirs['perm'], exist_ok=True)

    return dirs

##########################################################################################
# Readers of NEMO output

def readmf_T(expname, startyear, endyear):
    """ read multiple T_grid fields """

    dirs = folders(expname)
    filelist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_T, use_cftime=True)

    return data

def readmf_var_T(expname, startyear, endyear, var):
    """ read multiple T_grid fields extracted using CDO """

    dirs = folders(expname)
    filelist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['perm'], var, f"{var}_*_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_T, use_cftime=True)

    return data

def readmf_ice(expname, startyear, endyear):
    """ read multiple ice fields """

    dirs = folders(expname)
    filelist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_ice_*_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_ice, use_cftime=True)

    return data

def read_T(expname, year):
    """ read single T_grid field """

    dirs = folders(expname)
    filelist = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_T, use_cftime=True)
    
    return data

def read_ice(expname, year):
    """ read single ice field """

    dirs = folders(expname)
    filelist = os.path.join(dirs['nemo'], f"{expname}_ice_*_{year}-{year}.nc")
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_ice, use_cftime=True)
    
    return data

def read_domain(expname):
    """ read NEMO domain configuration file """

    dirs = folders(expname)
    filename = os.path.join(dirs['exp'], 'domain_cfg.nc')
    domain = xr.open_mfdataset(filename, preprocess=preproc_nemo_domain)
    domain = domain.isel(time=0)

    return domain

##########################################################################################
# Pre-processing options for NEMO readers

def preproc_nemo_domain(data):
    """ preprocessing routine for nemo domain """

    data = data.rename({'time_counter': 'time'})

    return data

def preproc_nemo_T(data):
    """ preprocessing routine for nemo for T grid """

    data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    data = data.rename({'nav_lat_grid_T': 'lat', 'nav_lon_grid_T': 'lon'})
    data = data.rename({'deptht': 'z', 'time_counter': 'time'})
    data = data.swap_dims({'x_grid_T_inner': 'x', 'y_grid_T_inner': 'y'})
    data = data.drop({'time_centered'})
    data = data.drop_dims({'axis_nbounds'})
    #data.coords['z'] = -data['z']
        
    return data

def preproc_nemo_U(data):
    """ preprocessing routine for nemo for U grid """

    data = data.rename_dims({'x_grid_U': 'x', 'y_grid_U': 'y'})
    data = data.rename({'depthu': 'z', 'time_counter': 'time'})
    data = data.swap_dims({'x_grid_U_inner': 'x', 'y_grid_U_inner': 'y'})
    
    return data

def preproc_nemo_V(data):
    """ preprocessing routine for nemo for V grid """

    data = data.rename_dims({'x_grid_V': 'x', 'y_grid_V': 'y'})
    data = data.rename({'depthv': 'z', 'time_counter': 'time'})
    data = data.swap_dims({'x_grid_V_inner': 'x', 'y_grid_V_inner': 'y'})
    
    return data

def preproc_nemo_W(data):
    """ preprocessing routine for nemo for W grid """

    data = data.swap_dims({'x_grid_W_inner': 'x', 'y_grid_W_inner': 'y'})
    data = data.rename_dims({'x_grid_W': 'x', 'y_grid_W': 'y'})
    data = data.rename({'depthw': 'z', 'time_counter': 'time'})

    return data

def preproc_nemo_ice(data):
    """ preprocessing routine for nemo for ice """

    data = data.rename({'time_counter': 'time'})
    
    return data

##########################################################################################
# Readers of averaged data: timeseries, profiles, maps, hovmoller, pdfs etc ...

def read_timeseries_T(expname, startyear, endyear, var):
    """ read averaged timeseries (for generic grid) """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"timeseries_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_profile_T(expname, startyear, endyear, var):
    """ read averaged profiles """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"profiles_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_hovmoller_T(expname, startyear, endyear, var):
    """ read averaged hovmoller diagram """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"hovmoller_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_map_T(expname, startyear, endyear, var):
    """read averaged map """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"map_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_field_T(expname, startyear, endyear, var):
    """read averaged meanfield in 2D or 3D """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"field_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

#### for anomaly

def read_timeseries_local_anomaly_T(expname, startyear, endyear, var):
    """ read averaged rms local anomaly timeseries """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"timeseries_local_anomaly_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_profile_local_anomaly_T(expname, startyear, endyear, var):
    """ read averaged profiles of rms local anomaly """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"profiles_local_anomaly_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_hovmoller_local_anomaly_T(expname, startyear, endyear, var):
    """ read averaged rms local anomaly hovmoller diagram """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"hovmoller_local_anomaly_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_map_local_anomaly_T(expname, startyear, endyear, var):
    """read averaged map of rms local anomaly """

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"map_local_anomaly_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

##########################################################################################
# Containers for reader/creator of averaged data

# for averaged timeseries
def read_averaged_timeseries_T(expname, startyear, endyear, inivar, ndim, isub, iload):
    """ reader/creator of averaged timeseries for T grid """

    # check if var is a new variable defined on a subregion
    if '-' in inivar:
        var = inivar.split('-')[0]
    else:
        var = inivar

    dirs = folders(expname)
    df = gm.elements(expname)

    # try to read averaged data
    try:
        data = read_timeseries_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    if iload == 'orig':
        data = readmf_T(expname, startyear, endyear)
        print(" Averaging ... ")
        tvec = gt.dateDecimal(data['time'].values)
        vec = gm.spacemean(expname, data[var], ndim)
    elif iload == 'post':
        data = read_from_cdo_T(expname, startyear, endyear, var)
        tvec = gt.dateDecimal(data['time'].values)
        vec = gm.spacemean(expname, data[var], ndim)

    # ONLY for 3D variables! 
    # compute var in subregions: mixed layer (mix), pycnocline (pyc), abyss (aby)
    if isub == True:
        subvec = gm.spacemean3d_suball(expname, data[var])
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                            attrs = {'units' : 'years', 'long_name' : 'years'}),
            var : xr.DataArray(data = vec, dims = ['time'], coords = {'time': tvec}, 
                            attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name}),                            
            var+'-mix' : xr.DataArray(data = subvec[0], dims = ['time'], coords = {'time': tvec}, 
                            attrs  = {'units' : data[var].units, 'long_name' : 'mixed layer ' + data[var].long_name}), 
            var+'-pyc' : xr.DataArray(data = subvec[1], dims = ['time'], coords = {'time': tvec}, 
                            attrs  = {'units' : data[var].units, 'long_name' : 'pycnocline ' + data[var].long_name}), 
            var+'-aby' : xr.DataArray(data = subvec[2], dims = ['time'], coords = {'time': tvec}, 
                            attrs  = {'units' : data[var].units, 'long_name' : 'abyss ' + data[var].long_name})},
            attrs = {'description': 'ECE4/NEMO 1D timeseries averaged from T_grid variables'})
        
        # write the averaged data and read it again
        print(" Saving averaged data ... ")
        filename = os.path.join(dirs['perm'], f"timeseries_{var}_{startyear}-{endyear}.nc")
        ds.to_netcdf(filename)
        data = read_timeseries_T(expname, startyear, endyear, var)

        return data

    # create xarray dataset
    ds = xr.Dataset({
        'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                        attrs = {'units' : 'years', 'long_name' : 'years'}), 
        var : xr.DataArray(data = vec, dims = ['time'], coords = {'time': tvec}, 
                        attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})},
        attrs = {'description': 'ECE4/NEMO 1D timeseries averaged from T_grid variables'})

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"timeseries_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)
    data = read_timeseries_T(expname, startyear, endyear, var)

    return data

# for averaged profiles
def read_averaged_profile_T(expname, startyear, endyear, var, iload):
    """ reader/creator of averaged profiles for T grid """

    dirs = folders(expname)
    df = gm.elements(expname)

    # try to read averaged data
    try:
        data = read_profile_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    if iload == 'orig':
        data = readmf_T(expname, startyear, endyear)
        print(" Averaging ... ")
        # and spatial averaging of the desidered variable
        zvec = data['z'].values.flatten()
        vec = data[var].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
    elif iload == 'post':
        data = read_from_cdo_T(expname, startyear, endyear, var)
        zvec = data['z'].values.flatten()
        vec = data[var].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()

    # create xarray dataset
    ds = xr.Dataset({
        'z': xr.DataArray(data = zvec, dims = ['z'], coords = {'z': zvec}, 
                             attrs = {'units' : 'm', 'long_name' : 'depth'}), 
        var : xr.DataArray(data = vec, dims = ['z'], coords = {'z': zvec}, 
                               attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})}, 
        attrs = {'description': 'ECE4/NEMO 1D averaged profiles from T_grid variables'})

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"profiles_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)    
    data = read_profile_T(expname, startyear, endyear, var)

    return data

# for averaged hovmöller diagram
def read_averaged_hovmoller_T(expname, startyear, endyear, var):
    """ reader/creator of averaged hovmöller diagram for T grid """

    dirs = folders(expname)
    df = gm.elements(expname)

    # try to read averaged data
    try:
        data = read_hovmoller_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    data = readmf_T(expname, startyear, endyear)
    print(" Averaging ... ")
    # and spatial averaging of the desidered variable
    tvec = gt.dateDecimal(data['time'].values)
    vec = gm.spacemean(expname, data[var], '2D')

    # create xarray dataset
    print(" Allocating new xarray dataset ... ")
    ds = xr.Dataset({
        'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                    attrs = {'units' : 'years', 'long_name' : 'years'}), 
        'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']}, 
                    attrs = {'units' : 'm', 'long_name' : 'depth'}), 
        var : xr.DataArray(data = vec, dims = ['time', 'z'], coords = {'time': tvec, 'z': data['z']},
                        attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})}, 
            attrs = {'description': 'ECE4/NEMO averaged T_grid 2D hovmoller diagram'})

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"hovmoller_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)
    data = read_field_T(expname, startyear, endyear, var)

    return data

# for averaged field
def read_averaged_field_T(expname, startyear, endyear, var, ndim):
    """ reader/creator of averaged field for T grid """

    dirs = folders(expname)
    df = gm.elements(expname)

    # try to read averaged data
    try:
        data = read_field_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    data = readmf_T(expname, startyear, endyear)
    print(" Averaging ... ")
    # and spatial averaging of the desidered variable
    vec = gm.timemean(data[var])

    # create xarray dataset
    print(" Allocating new xarray dataset ... ")
    if ndim == '3D':
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']},
                        attrs = {'units' : 'm', 'long_name' : 'depth'}),                             
            var : xr.DataArray(data = vec, dims = ['z', 'y', 'x'], coords = {'z': data['z'], 'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})}, 
            attrs = {'description': 'ECE4/NEMO averaged T_grid_3D field'})

    if ndim == '2D':
        ds = xr.Dataset({
            'lat': xr.DataArray(data = data['lat'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'latitude'}),
            'lon': xr.DataArray(data = data['lon'], dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']}, 
                        attrs = {'units' : 'deg', 'long_name' : 'longitude'}),                   
            var : xr.DataArray(data = vec, dims = ['y', 'x'], coords = {'y': data['y'], 'x': data['x']},
                        attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})}, 
            attrs = {'description': 'ECE4/NEMO averaged T_grid_2D field'})

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"field_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)
    data = read_field_T(expname, startyear, endyear, var)

    return data

##################################################################################################################
# reader/creator of averaged local anomaly

# timeseries of averaged rms local anomaly
def read_averaged_timeseries_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var, ndim):
    """ reader/creator of averaged timeseries of rms local anomaly for T grid """

    dirs = folders(expname)
    df = gm.elements(expname)

    # try to read averaged data
    try:
        data = read_timeseries_local_anomaly_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    # read field and meanfield
    mdata = read_averaged_field_T(refname, startref, endref, var, ndim)
    data = readmf_T(expname, startyear, endyear)
    delta = np.square(data[var]-mdata[var]) # choose cost function: square
    
    print(" Averaging ... ")
    # spatial averaging of the desidered variable
    tvec = gt.dateDecimal(data['time'].values)
    vec = gm.spacemean(expname, delta, ndim)
    vec = np.power(vec,0.5)

    # create xarray dataset
    ds = xr.Dataset({
        'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                        attrs = {'units' : 'years', 'long_name' : 'years'}), 
        var : xr.DataArray(data = vec, dims = ['time'], coords = {'time': tvec}, 
                        attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})},
        attrs = {'description': 'ECE4/NEMO 1D timeseries averaged rms local anomaly from T_grid variables'})

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"timeseries_local_anomaly_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)
    data = read_timeseries_local_anomaly_T(expname, startyear, endyear, var)

    return data

# profile of the anomaly 
def read_averaged_profile_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var):
    """ reader/creator of averaged profile of rms local anomaly for T grid """

    dirs = folders(expname)
    df = gm.elements(expname)    

    # try to read averaged data
    try:
        data = read_profile_local_anomaly_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    # read field and meanfield
    mdata = read_averaged_field_T(refname, startref, endref, var, '3D')
    data = readmf_T(expname, startyear, endyear)
    delta = np.power(data[var]-mdata[var],2) # choose cost function: square

    print(" Averaging ... ")
    # and spatial averaging of the desidered variable
    zvec = data['z'].values.flatten()
    vec = delta.weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
    vec = np.power(vec,0.5)

    # create xarray dataset
    print(" Allocating new xarray dataset ... ")
    ds = xr.Dataset({
        'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']}, 
                    attrs = {'units' : 'm', 'long_name' : 'depth'}), 
        var : xr.DataArray(data = vec, dims = ['z'], coords = {'z': data['z']},
                    attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})
                    }, 
        attrs = {'description': 'ECE4/NEMO averaged T_grid 2D profile of rms local anomaly'}
        )

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"hovmoller_local_anomaly_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)
    data = read_hovmoller_local_anomaly_T(expname, startyear, endyear, var)

    return data

# howmoller diagram of averaged rms local anomaly
def read_averaged_hovmoller_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var):
    """ reader/creator of averaged hovmöller diagram of rms local anomaly for T grid """

    dirs = folders(expname)
    
    # try to read averaged data
    try:
        data = read_hovmoller_local_anomaly_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    # read field and meanfield
    mdata = read_averaged_field_T(refname, startref, endref, var, '3D')
    data = readmf_T(expname, startyear, endyear)
    delta = np.power(data[var]-mdata[var],2) # choose cost function: square

    print(" Averaging ... ")
    # and spatial averaging of the desidered variable
    tvec = gt.dateDecimal(data['time'].values)
    vec = gm.spacemean(expname, delta, '2D')
    vec = np.power(vec,0.5)

    # create xarray dataset
    print(" Allocating new xarray dataset ... ")
    ds = xr.Dataset({
        'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                    attrs = {'units' : 'years', 'long_name' : 'years'}), 
        'z': xr.DataArray(data = data['z'], dims = ['z'], coords = {'z': data['z']}, 
                    attrs = {'units' : 'm', 'long_name' : 'depth'}), 
        var : xr.DataArray(data = vec, dims = ['time', 'z'], coords = {'time': tvec, 'z': data['z']},
                    attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})
                    }, 
        attrs = {'description': 'ECE4/NEMO averaged T_grid 2D hovmoller diagram of rms local anomaly'}
        )

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"hovmoller_local_anomaly_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)
    data = read_hovmoller_local_anomaly_T(expname, startyear, endyear, var)

    return data


##########################################################################################
# OPEN ISSUES:

# - merger of long simulations
# - append new data on existing averaged file
# - saving figure and launch functions for command line

##########################################################################################

# Read from CDO

def read_from_cdo_T(expname, startyear, endyear, var):
    """  read field extracted using with CDO """

    data = readmf_var_T(expname, startyear, endyear, var)

    return data
