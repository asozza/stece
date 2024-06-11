#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for i/o operations

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import subprocess
import os
import glob
import shutil
import yaml
import dask
import cftime
import nc_time_axis
import netCDF4
import numpy as np
import xarray as xr

import osprey.means.means as osm

import osprey_io as osi
import osprey_tools as ost
import osprey_actions as osa


##########################################################################################
# Pre-processing options for EOF reader

def preproc_timeseries_3D(data):
    """ preprocessing routine for EOF timeseries """

    data = data.rename({'time_counter': 'time', 'deptht': 'z'})
    data = data.drop_vars({'time_counter_bnds', 'deptht_bnds'})
        
    return data

def preproc_timeseries_2D(data):
    """ preprocessing routine for EOF timeseries """

    data = data.rename({'time_counter': 'time'})
    data = data.drop_vars({'time_counter_bnds'})
        
    return data

def preproc_pattern_3D(data):
    """ preprocessing routine for EOF pattern """

    data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    data = data.rename({'nav_lat_grid_T': 'lat', 'nav_lon_grid_T': 'lon'})
    data = data.rename({'time_counter': 'time', 'deptht': 'z'})
    data = data.drop_vars({'time_counter_bnds', 'deptht_bnds'})
    
    return data

def preproc_pattern_2D(data):
    """ preprocessing routine for EOF pattern """

    data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    data = data.rename({'nav_lat_grid_T': 'lat', 'nav_lon_grid_T': 'lon'})
    data = data.rename({'time_counter': 'time'})
    data = data.drop_vars({'time_counter_bnds'})

    return data

def preproc_variance(data):
    """ preprocessing routine for EOF variance """

    data = data.rename({'time_counter': 'time'})
    data = data.drop_vars({'time_counter_bnds'})
        
    return data

def postproc_field_2D(data):
    """ postprocessing routime for field from EOF """

    data = data.rename_dims({'x': 'x_grid_T', 'y': 'y_grid_T'})
    data = data.rename({'lat': 'nav_lat_grid_T', 'lon': 'nav_lon_grid_T'})
    data = data.rename({'time': 'time_counter'})
        
    return data

def postproc_field_3D(data):
    """ postprocessing routime for field from EOF """

    data = data.rename_dims({'x': 'x_grid_T', 'y': 'y_grid_T'})
    data = data.rename({'lat': 'nav_lat_grid_T', 'lon': 'nav_lon_grid_T'})
    data = data.rename({'time': 'time_counter'})
    data = data.rename({'z': 'deptht'})

    return data

def preproc_forecast_3D(data):
    """ preprocessing routine for EOF pattern """

    data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    data = data.rename({'nav_lat_grid_T': 'nav_lat', 'nav_lon_grid_T': 'nav_lon'})
    data = data.rename({'deptht': 'nav_lev'})
    data = data.expand_dims(time_counter=1)
    nav_lon_expanded = data["nav_lon"].expand_dims(time_counter=data.coords['time_counter'])
    nav_lat_expanded = data["nav_lat"].expand_dims(time_counter=data.coords['time_counter'])
    data_expanded_coords = data.assign_coords(nav_lon=nav_lon_expanded, nav_lat=nav_lat_expanded)
    data = data_expanded_coords.reset_coords(["nav_lon", "nav_lat"])
    
    return data

##########################################################################################
# CDO commands

def cdo_merge(expname, startyear, endyear):
    """ CDO command to merge files """

    dirs = osi.folders(expname)
    leg = ost.get_leg(endyear)

    fldlist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        fldlist.extend(matching_files)
    
    fldcat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{expname}_{startyear}-{endyear}.nc")
    ost.run_bash_command(f"cdo cat {' '.join(fldlist)} {fldcat}")

    return None

def cdo_selname(expname, startyear, endyear, var):
    """ CDO command to select variable """

    dirs = osi.folders(expname)
    leg = ost.get_leg(endyear)    

    fld = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    fldcat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{expname}_{startyear}-{endyear}.nc")

    ost.run_bash_command(f"cdo yearmean -selname,{var} {fldcat} {fld}")

    return None

def cdo_detrend(expname, startyear, endyear, var):
    """ CDO command to detrend, subtracting time average """

    dirs = osi.folders(expname)
    leg = ost.get_leg(endyear)

    fld = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_{startyear}-{endyear}.nc")   
    flda = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly_{startyear}-{endyear}.nc")

    ost.run_bash_command(f"cdo sub {fld} -timmean {fld} {flda}")

    return None

def cdo_EOF(expname, startyear, endyear, var, ndim):
    """ CDO command to compute EOF """
    
    dirs = osi.folders(expname)
    leg = ost.get_leg(endyear)
    window = endyear - startyear

    flda = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly_{startyear}-{endyear}.nc")    
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance_{startyear}-{endyear}.nc")
    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc")

    try:
        os.remove(fldcov)
        print(f"File {fldcov} successfully removed.")
    except FileNotFoundError:
        print(f"File {fldcov} not found. Unable to remove.")

    try:
        os.remove(fldpat)
        print(f"File {fldpat} successfully removed.")
    except FileNotFoundError:
        print(f"File {fldpat} not found. Unable to remove.")

    if ndim == '2D':
        ost.run_bash_command(f"cdo eof,{window} {flda} {fldcov} {fldpat}")
    
    if ndim == '3D':
        ost.run_bash_command(f"cdo eof3d,{window} {flda} {fldcov} {fldpat}")

    timeseries = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_timeseries_{startyear}-{endyear}_")
    ost.run_bash_command(f"cdo eofcoeff {fldpat} {flda} {timeseries}")

    return None

def cdo_retrend(expname, startyear, endyear, var):
    """ CDO command to add trend """

    dirs = osi.folders(expname)
    endleg = ost.get_leg(endyear)

    fld = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    flda = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast_{startyear}-{endyear}.nc")
    ost.run_bash_command(f"cdo add {flda} -timmean {fld} {flda}")

    return None

def cdo_info_EOF(expname, startyear, endyear, var):

    dirs = osi.folders(expname)
    leg = ost.get_leg(endyear)

    cov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance_{startyear}-{endyear}.nc")

    ost.run_bash_command(f"cdo info -div {cov} -timsum {cov}")

    return None

##########################################################################################
# Reader of EOF

def create_EOF(expname, startyear, endyear, var, ndim):
    """ Create EOF """

    cdo_merge(expname, startyear, endyear)
    cdo_selname(expname, startyear, endyear, var)
    cdo_detrend(expname, startyear, endyear, var)
    cdo_EOF(expname, startyear, endyear, var, ndim)

    return None


def save_EOF(expname, startyear, endyear, field, var, ndim):
    """" save new field from EOF """

    dirs = osi.folders(expname)
    endleg = ost.get_leg(endyear)

    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_product_{startyear}-{endyear}.nc")

    try:
        os.remove(filename)
        print(f"File {filename} successfully removed.")
    except FileNotFoundError:
        print(f"File {filename} not found. Unable to remove.")

    if ndim == '2D':
        field = postproc_field_2D(field)
    if ndim == '3D':
        field = postproc_field_3D(field)

    field.to_netcdf(filename, mode='w', unlimited_dims={'time_counter': True})

    return None


def add_trend_EOF(expname, startyear, endyear, var):

    dirs = osi.folders(expname)
    endleg = ost.get_leg(endyear)

    # add mean time trend to the anomaly 
    inifile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    auxfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_product_{startyear}-{endyear}.nc")
    newfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast_{startyear}-{endyear}.nc")

    try:
        os.remove(newfile)
        print(f"File {newfile} successfully removed.")
    except FileNotFoundError:
        print(f"File {newfile} not found. Unable to remove.")

    ost.run_bash_command(f"cdo add {auxfile} -timmean {inifile} {newfile}")

    return None

##########################################################################################
