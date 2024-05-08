#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for i/o operations

Authors
Alessandro Sozza (CNR-ISAC, Mar 2024)
"""

import subprocess
import numpy as np
import os
import glob
import shutil
import yaml
import numpy as np
import xarray as xr
import cftime

def folders(expname):

    dirs = {
        'exp': os.path.join("/ec/res4/scratch/itas/ece4", expname),
        'nemo': os.path.join("/ec/res4/scratch/itas/ece4/", expname, "output", "nemo"),
        'restart': os.path.join("/ec/res4/scratch/itas/ece4/", expname, "restart"),        
        'tmp':  os.path.join("/ec/res4/scratch/itas/martini", expname),
        'rebuild': "/ec/res4/hpcperm/itas/src/rebuild_nemo",
        'backup': os.path.join("/ec/res4/scratch/itas/ece4", expname + "-backup")
    }

    return dirs

def preproc_nemo_T(data):
    """preprocessing routine for nemo for T grid"""

    data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    data = data.swap_dims({'x_grid_T_inner': 'x', 'y_grid_T_inner': 'y'})
    data = data.rename({'deptht': 'z', 'time_counter': 'time', 'thetao': 'to'})    
    data = data.rename({'nav_lat_grid_T': 'nav_lat', 'nav_lon_grid_T': 'nav_lon'})
    data.coords['z'] = -data['z']
    
    return data

def preproc_nemo_restart(data):
    """preprocessing routine for nemo restart grid"""

    data = data.rename_dims({'nav_lev': 'z', 'time_counter': 'time'})
    data = data.rename({'nav_lat': 'lat', 'nav_lon': 'lon'})

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

def read_restart(expname, leg):

    dirs = folders(expname)
    filename = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc')
    data = xr.open_mfdataset(filename)

    return data

def get_nemo_timestep(filename):
    """Minimal function to get the timestep from a nemo restart file"""

    return os.path.basename(filename).split('_')[1]

def start_end_years(expname, yearspan, leg):

    dirs = folders(expname)

    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)
    info = leginfo['base.context']['experiment']['schedule']['leg']
    endyear = info['start'].year - 1
    startyear = endyear - yearspan

    return startyear,endyear

def write_nemo_restart(expname, field, leg):

    dirs = folders(expname)
    flist = glob.glob(os.path.join(dirs['restart'], str(leg).zfill(3), expname + '*_' + 'restart' + '_????.nc'))
    timestep = get_nemo_timestep(flist[0])

    # ocean restart creation
    oceout = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart.nc')
    field.to_netcdf(oceout, mode='w', unlimited_dims={'time_counter':True})

    # copy ice restart
    #orig = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart_ice.nc')
    orig = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '_' + timestep + '_restart_ice.nc')
    dest = os.path.join(dirs['tmp'], str(leg).zfill(3), 'restart_ice.nc')
    shutil.copy(orig, dest)
