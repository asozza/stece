#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EOF module

Author: Alessandro Sozza (CNR-ISAC) 
Date: May 2024
"""

import os
import glob
import xarray as xr

from osprey.utils.folders import folders
from osprey.utils.time import get_leg
from osprey.utils import run_cdo
from osprey.utils.utils import remove_existing_file
from osprey.means.means import globalmean

##########################################################################################
# Pre-processing options for EOF reader

def preproc_timeseries_3D(data):
    """ preprocessing routine for EOF timeseries """

    data = data.rename({'time_counter': 'time'})
    data = data.isel(lon=0,lat=0,zaxis_Reduced=0)
    data = data.drop_vars({'time_counter_bnds','lon','lat','zaxis_Reduced'})

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

def postproc_var_3D(data):
    
    data = data.rename({'time': 'time_counter', 'z': 'nav_lev'})

    return data

##########################################################################################
# Reader of EOF

def detrend_3D(expname, startyear, endyear, var):

    dirs = folders(expname)
    endleg = get_leg(endyear)

    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    #filename = os.path.join(f"{var}_{startyear}-{endyear}.nc")
    data = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_var_3D)
    ave = globalmean(data, var, '2D')
    data[var] = data[var] - ave
    data = postproc_var_3D(data)
    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_anom_{startyear}-{endyear}.nc")
    #filename=os.path.join(f"{var}_anomaly_{startyear}-{endyear}.nc")
    remove_existing_file(filename)
    data.to_netcdf(filename, mode='w', unlimited_dims={'time_counter': True})

    return None

def retrend_3D(expname, startyear, endyear, var):

    dirs = folders(expname)
    endleg = get_leg(endyear)

    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    #filename = os.path.join(f"{var}_{startyear}-{endyear}.nc")
    data = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_var_3D)
    ave = globalmean(data, var, '2D')
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_prod_{startyear}-{endyear}.nc")
    #filename = os.path.join(f"{var}_product_{startyear}-{endyear}.nc")
    data = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_var_3D)
    data[var] = data[var] + ave
    data = postproc_var_3D(data)
    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_fore_{startyear}-{endyear}.nc")
    #filename=os.path.join(f"{var}_forecast_{startyear}-{endyear}.nc")
    remove_existing_file(filename)
    data.to_netcdf(filename, mode='w', unlimited_dims={'time_counter': True})    

    return None


def create_EOF(expname, startyear, endyear, var, ndim):
    """ Create EOF """

    run_cdo.merge(expname, startyear, endyear)
    run_cdo.selname(expname, startyear, endyear, var)
    run_cdo.detrend(expname, startyear, endyear, var)
    run_cdo.get_EOF(expname, startyear, endyear, var, ndim)

    return None


def save_EOF(expname, startyear, endyear, field, var):
    """" save new field from EOF """
    
    dirs = folders(expname)
    endleg = get_leg(endyear)

    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_product.nc")
    remove_existing_file(filename)
    
    #if ndim == '2D':
    #    field = postproc_field_2D(field)
    #if ndim == '3D':
    field = postproc_field_3D(field)

    field.to_netcdf(filename, mode='w', unlimited_dims={'time_counter': True})

    return None


##########################################################################################
