#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EOF module

Author: Alessandro Sozza (CNR-ISAC) 
Date: May 2024
"""

import os
import glob
import subprocess
import numpy as np
import xarray as xr
import cftime

from osprey.utils.folders import folders
from osprey.utils.time import get_leg
from osprey.utils import run_cdo_old
from osprey.utils.utils import remove_existing_file
from osprey.means.means import globalmean
from osprey.utils.vardict import vardict

def _forecast_xarray(foreyear):
    """Get the xarray for the forecast time"""
    
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 0, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])},
                      attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    return xf

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


def process_data(data, mode, dim='3D'):
    """
    Function for preprocessing or postprocessing 2D/3D data.

    Parameters:
    - data: xarray.DataArray or xarray.Dataset
        Input data to be processed.
    - mode: str
        Operation mode. Choose from:
        'pattern' - Preprocessing for EOF pattern.
        'timeseries' - Preprocessing for EOF timeseries.
        'postprocess' - Post-processing for variable field.
    - dim: str, optional (default='3D')
        Dimensionality of the dataset. Choose from '2D' or '3D'.

    Returns:
    - Processed data (xarray.DataArray or xarray.Dataset)
    """

    if dim not in {'2D', '3D'}:
        raise ValueError(f"Invalid dim '{dim}'. Choose '2D' or '3D'.")

    if mode == 'pattern':
        # Preprocessing routine for EOF pattern
        data = data.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
        data = data.rename({'nav_lat_grid_T': 'lat', 'nav_lon_grid_T': 'lon'})
        data = data.rename({'time_counter': 'time'})
        data = data.drop_vars({'time_counter_bnds'}, errors='ignore')
        if dim == '3D':
            data = data.rename({'deptht': 'z'})
            data = data.drop_vars({'deptht_bnds'}, errors='ignore')        

    elif mode == 'series':
        # Preprocessing routine for EOF timeseries
        data = data.rename({'time_counter': 'time'})
        data = data.isel(lon=0, lat=0)
        data = data.drop_vars({'time_counter_bnds', 'lon', 'lat'}, errors='ignore')
        if dim == '3D':
            data = data.isel(zaxis_Reduced=0)
            data = data.drop_vars({'zaxis_Reduced'}, errors='ignore')

    elif mode == 'post':
        # Post-processing routine for variable field
        data = data.rename({'time': 'time_counter'})
        if dim == '3D':
            data = data.rename({'z': 'nav_lev'})

    else:
        raise ValueError(f"Invalid mode '{mode}'. Choose from 'pattern', 'tseries', or 'postproc'.")

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

def project_eofs(dir, varname, neofs, xf, mode):
    """ 
    Function to project a field in the future using EOFs. 
    
    Different options are available:
    - projection using the full set of EOFs (mode=full)
    - projection using only the first EOF (mode=first)
    - projection using EOFs up to a percentage of the full (mode=frac)
    - reconstruction of the original field using EOFs (mode=reco)
    
    """

    info = vardict('nemo')[varname]

    print(dir)
    filename = os.path.join(dir, f"{varname}_pattern.nc")
    pattern = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='pattern', dim=info['dim']))
    field = pattern.isel(time=0)*0

    if mode == 'standard':
        for i in range(neofs):
            filename = os.path.join(dir, f"{varname}_series_0000{i}.nc")    
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='series', dim=info['dim']))        
            p = timeseries.polyfit(dim='time', deg=1, skipna = True)
            theta = xr.polyval(xf, p[f"{varname}_polyfit_coefficients"])
            basis = pattern.isel(time=i)
            field = field + theta*basis        

    elif mode == 'first':
        filename = os.path.join(dir, f"{varname}_series_00000.nc")    
        timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='series', dim=info['dim']))        
        p = timeseries.polyfit(dim='time', deg=1, skipna = True)
        theta = xr.polyval(xf, p[f"{varname}_polyfit_coefficients"])
        basis = pattern.isel(time=i)
        field = field + theta*basis                

    elif mode == 'reco':

        for i in range(neofs):
            filename = os.path.join(dir, f"{varname}_series_0000{i}.nc")    
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='series', dim=info['dim']))
            theta = timeseries[varname].isel(time=-1)
            basis = pattern.isel(time=i)
            field = field + theta*basis

        # add figure


    elif mode == 'frac':
        
        threshold_percentage = 0.9

        weights = []
        cdo_command = f"cdo info -div {varname}_variance.nc -timsum {varname}_variance.nc"
        output = subprocess.check_output(cdo_command, shell=True, text=True)
        for line in output.splitlines():
            if "Mean" in line:
                mean_value = float(line.split(":")[3].strip())
                weights.append(mean_value)
        weights = np.array(weights)
        cumulative_weights = np.cumsum(weights) / np.sum(weights)

        # Find the index where cumulative sum exceeds the threshold percentage
        feofs = np.searchsorted(cumulative_weights, threshold_percentage) + 1

        for i in range(feofs):
            filename = os.path.join(dir, f"{varname}_series_0000{i}.nc")
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='series', dim=info['dim']))
            p = timeseries.polyfit(dim='time', deg=1, skipna=True)
            theta = xr.polyval(xf, p[f"{varname}_polyfit_coefficients"])
            basis = pattern.isel(time=i)
            field += theta * basis        


    return field