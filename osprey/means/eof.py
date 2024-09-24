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

def get_eof_winter_only(expname, startyear, endyear):
    """
    Process NEMO output files, select winter months, compute EOF using sklearn PCA.
    
    Parameters:
    - expname: experiment name.
    - startyear: the starting year.
    - endyear: the ending year.

    """

    dirs = folders(expname)

    # Step 1: Load the data with xarray
    files = []
    for year in range(startyear, endyear + 1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        files.extend(glob.glob(pattern))

    ds = xr.open_mfdataset(files, combine='by_coords')

    # Step 2: Select only December and January data
    ds_winter = ds.groupby('time.month').filter(lambda x: x.month in [12, 1])

    # Remove the first January and last December
    ds_winter = ds_winter.where(~((ds_winter['time.month'] == 1) & (ds_winter['time.year'] == startyear)), drop=True)
    ds_winter = ds_winter.where(~((ds_winter['time.month'] == 12) & (ds_winter['time.year'] == endyear)), drop=True)

    # Step 3: Calculate moving average
    ds_winter_avg = ds_winter.rolling(time=2, center=True).mean().dropna('time', how='all')

    # Step 4: Flatten the spatial dimensions for EOF calculation
    # Assuming ds_winter_avg has dimensions ('time', 'lat', 'lon')
    time_len = ds_winter_avg.time.size
    lat_len = ds_winter_avg.lat.size
    lon_len = ds_winter_avg.lon.size

    # Reshape the data into 2D (time, space) for PCA
    reshaped_data = ds_winter_avg.values.reshape(time_len, lat_len * lon_len)

    # Step 5: 
    # Standardize the data (optional but recommended)
    #reshaped_data = (reshaped_data - np.mean(reshaped_data, axis=0)) / np.std(reshaped_data, axis=0)
    # Compute anomaly
    reshaped_data = (reshaped_data - np.mean(reshaped_data, axis=0))

    # Step 6: Compute EOF using PCA
    pca = PCA(n_components=3)  # You can adjust the number of EOFs here
    pca.fit(reshaped_data)

    # Get the EOFs (principal components) and the explained variance
    eof_patterns = pca.components_.reshape(3, lat_len, lon_len)  # reshape back to spatial dimensions
    explained_variance = pca.explained_variance_ratio_

    # Return EOF patterns and explained variance
    return eof_patterns, explained_variance