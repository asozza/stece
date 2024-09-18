#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EOF module

Author: Alessandro Sozza (CNR-ISAC) 
Date: May 2024
"""

import os
import glob
import numpy as np
import xarray as xr
import cftime

from osprey.utils.folders import folders
from osprey.utils.time import get_leg
from osprey.utils import run_cdo_old
from osprey.utils.utils import remove_existing_file
from osprey.means.means import globalmean

def _time_xarray(startyear, endyear):
    """Reconstruct the time array of restarts"""

    dates=[]
    for year in range(startyear,endyear+1):
        x = cftime.DatetimeGregorian(year, 1, 1, 0, 0, 0, has_year_zero=False)
        dates.append(x)
    tdata = xr.DataArray(data = np.array(dates), dims = ['time_counter'], coords = {'time_counter': np.array(dates)}, 
                         attrs = {'stardand_name': 'time', 'axis': 'T'})

    return tdata

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

def detrend_3D(expname, startyear, endyear, var):

    dirs = folders(expname)
    endleg = get_leg(endyear)

    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    data = xr.open_mfdataset(filename, use_cftime=True)
    ave = globalmean(data, var, '2D')
    data[var] = data[var] - ave
    data = postproc_var_3D(data)
    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_anom_{startyear}-{endyear}.nc")
    remove_existing_file(filename)
    data.to_netcdf(filename, mode='w', unlimited_dims={'time_counter': True})

    return None

def retrend_3D(expname, startyear, endyear, var):

    dirs = folders(expname)
    endleg = get_leg(endyear)

    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    data = xr.open_mfdataset(filename, use_cftime=True)
    ave = globalmean(data, var, '2D')
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_prod_{startyear}-{endyear}.nc")
    data = xr.open_mfdataset(filename, use_cftime=True)
    data[var] = data[var] + ave
    data = postproc_var_3D(data)
    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_fore_{startyear}-{endyear}.nc")
    remove_existing_file(filename)
    data.to_netcdf(filename, mode='w', unlimited_dims={'time_counter': True})    

    return None

##########################################################################################

def create_EOF(expname, startyear, endyear, var, ndim):
    """ Create EOF """

    run_cdo_old.merge(expname, startyear, endyear)
    run_cdo_old.selname(expname, startyear, endyear, var)
    run_cdo_old.detrend(expname, startyear, endyear, var)
    run_cdo_old.get_EOF(expname, startyear, endyear, var, ndim)

    return None


def change_timeaxis(expname, var, startyear, endyear):

    dirs = folders(expname)
    endleg = get_leg(endyear)
    tdata = _time_xarray(startyear, endyear)

    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_nt.nc")
    data = xr.open_mfdataset(filename, use_cftime=True)
    data['time_counter'] = tdata

    filename=os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}.nc")
    remove_existing_file(filename)
    data.to_netcdf(filename, mode='w', unlimited_dims={'time_counter': True})

    return None


##########################################################################################
