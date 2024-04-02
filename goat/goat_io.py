#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
  ____   ____     _   _____
 / __/  / __ \   / \ |_   _|
| |  _ | |  | | / _ \  | |  
| |_| || |__| |/ /_\ \ | |  
 \____| \____//_/   \_\|_|  

GOAT: Global Ocean Analysis and Trends
------------------------------------------------------
GOAT library for i/o operations

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import subprocess
import os
import glob
import yaml
import numpy as np
import netCDF4
import xarray as xr
import cftime
import gc
from sklearn.linear_model import LinearRegression
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

    dirs = folders(expname)
    filelist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_T, use_cftime=True)

    return data

def readmf_ice(expname, startyear, endyear):

    dirs = folders(expname)
    filelist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_ice_*_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_ice, use_cftime=True)

    return data

def read_T(expname, year):

    dirs = folders(expname)
    filelist = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_T, use_cftime=True)
    
    return data

def read_ice(expname, year):

    dirs = folders(expname)
    filelist = os.path.join(dirs['nemo'], f"{expname}_ice_*_{year}-{year}.nc")
    data = xr.open_mfdataset(filelist, preprocess=preproc_nemo_ice, use_cftime=True)
    
    return data

def read_domain(expname):

    dirs = folders(expname)
    domain = xr.open_dataset(os.path.join(dirs['exp'], 'domain_cfg.nc'))

    return domain

##########################################################################################
# PREPROCESSING OPTIONS

def preproc_nemo_T(data):
    """preprocessing routine for nemo for T grid"""

    data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    data = data.rename({'deptht': 'z', 'time_counter': 'time'})
    data = data.swap_dims({'x_grid_T_inner': 'x', 'y_grid_T_inner': 'y'})
    data.coords['z'] = -data['z']
    
    return data

def preproc_nemo_U(data):
    """preprocessing routine for nemo for U grid"""

    data = data.rename_dims({'x_grid_U': 'x', 'y_grid_U': 'y'})
    data = data.rename({'depthu': 'z', 'time_counter': 'time'})
    data = data.swap_dims({'x_grid_U_inner': 'x', 'y_grid_U_inner': 'y'})
    data.coords['z'] = -data['z']
    
    return data

def preproc_nemo_V(data):
    """preprocessing routine for nemo for V grid"""

    data = data.rename_dims({'x_grid_V': 'x', 'y_grid_V': 'y'})
    data = data.rename({'depthv': 'z', 'time_counter': 'time'})
    data = data.swap_dims({'x_grid_V_inner': 'x', 'y_grid_V_inner': 'y'})
    data.coords['z'] = -data['z']
    
    return data

def preproc_nemo_W(data):
    """preprocessing routine for nemo for W grid"""

    data = data.swap_dims({'x_grid_W_inner': 'x', 'y_grid_W_inner': 'y'})
    data = data.rename_dims({'x_grid_W': 'x', 'y_grid_W': 'y'})
    data = data.rename({'depthw': 'z', 'time_counter': 'time'})
    data.coords['z'] = -data['z']

    return data

def preproc_nemo_ice(data):
    """preprocessing routine for nemo for ice"""

    data = data.rename({'time_counter': 'time'})
    
    return data

##########################################################################################
# Readers of averaged data: timeseries, profiles, maps, hovmoller, pdfs etc ...

def read_timeseries_T(expname, startyear, endyear, var):

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"timeseries_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_profile_T(expname, startyear, endyear, var):

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"profiles_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

def read_hovmoller_T(expname, startyear, endyear, var):

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"hovmoller_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

# 2d horizontal map: 
def read_map_T(expname, startyear, endyear, var):

    dirs = folders(expname)
    filename = os.path.join(dirs['perm'], f"map_{var}_{startyear}-{endyear}.nc")
    data = xr.open_dataset(filename, use_cftime=True)

    return data

##########################################################################################
# Containers for reader/creator of averaged data

def read_averaged_timeseries_T(expname, startyear, endyear, inivar, ndim, isub):

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
    data = readmf_T(expname, startyear, endyear)
    print(" Averaging ... ")
    # and spatial averaging of the desidered variable
    tvec = gt.dateDecimal(data['time'].values)
    vec = gm.spacemean(expname, data[var], ndim)
    
    if isub == True:
        subvec = gm.spacemean3d_suball(expname, data[var])
        ds = xr.Dataset({
            'time': xr.DataArray(data = tvec, dims = ['time'], coords = {'time': tvec}, 
                            attrs = {'units' : 'years', 'long_name' : 'years'}),            
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

def read_averaged_profile_T(expname, startyear, endyear, var):

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
    data = readmf_T(expname, startyear, endyear)
    print(" Averaging ... ")
    # and spatial averaging of the desidered variable
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

def read_averaged_map_T(expname, startyear, endyear, var):

    dirs = folders(expname)
    df = gm.elements(expname)

    # try to read averaged data
    try:
        data = read_map_T(expname, startyear, endyear, var)
        print(" Averaged data found ")
        return data
    except FileNotFoundError:
        print(" Averaged data not found. Creating new file ... ")

    # If averaged data not existing, read original data
    print(" Loading data ... ")
    data = readmf_T(expname, startyear, endyear)
    print(" Averaging ... ")
    # and spatial averaging of the desidered variable
    xvec = gt.dateDecimal(data['time'].values)
    yvec = data['z'].values.flatten()
    fvec = data[var].weighted(df['area']).mean(dim=['y', 'x']).values.flatten()
    vec = fvec.reshape(len(xvec),len(yvec))

    # create xarray dataset
    ds = xr.Dataset({
        'time': xr.DataArray(data = xvec, dims = ['time'], coords = {'time': xvec},                              
                             attrs = {'units' : 'years', 'long_name' : 'time'}), 
        'z': xr.DataArray(data = yvec, dims = ['z'], coords = {'z': yvec}, 
                             attrs = {'units' : 'm', 'long_name' : 'depth'}), 
        var : xr.DataArray(data = vec, dims = ['time', 'z'], coords = {'time': xvec, 'z': yvec}, 
                               attrs  = {'units' : data[var].units, 'long_name' : data[var].long_name})}, 
        attrs = {'description': 'ECE4/NEMO 2D averaged hovmoller diagram from T_grid variables'})

    # write the averaged data and read it again
    print(" Saving averaged data ... ")
    filename = os.path.join(dirs['perm'], f"map_{var}_{startyear}-{endyear}.nc")
    ds.to_netcdf(filename)    
    data = read_map_T(expname, startyear, endyear, var)

    return data