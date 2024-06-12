#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EOF module

Author: Alessandro Sozza (CNR-ISAC) 
Date: May 2024
"""

import os
import glob
from osprey.utils.folders import folders
from osprey.utils.utils import run_bash_command
from osprey.utils.time import get_leg
from osprey.utils import cdo

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
# Reader of EOF

def create_EOF(expname, startyear, endyear, var, ndim):
    """ Create EOF """

    cdo.merge(expname, startyear, endyear)
    cdo.selname(expname, startyear, endyear, var)
    cdo.detrend(expname, startyear, endyear, var)
    cdo.get_EOF(expname, startyear, endyear, var, ndim)

    return None


def save_EOF(expname, startyear, endyear, field, var, ndim):
    """" save new field from EOF """

    dirs = folders(expname)
    endleg = get_leg(endyear)

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


##########################################################################################
