#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forecasters Module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: Mar 2024
"""

import os
import numpy as np
from copy import deepcopy
import cftime
import xarray as xr

from osprey.utils.folders import folders
from osprey.utils.time import get_year, get_startleg, get_startyear, get_forecast_year
from osprey.actions.reader import reader_nemo, reader_rebuilt 
from osprey.actions.postreader import reader_restart
from osprey.means.eof import change_timeaxis, postproc_var_3D
from osprey.means.eof import preproc_pattern_2D, preproc_pattern_3D, preproc_timeseries_2D, preproc_timeseries_3D
from osprey.means.means import timemean
from osprey.utils import run_cdo_old
from osprey.utils.utils import remove_existing_file, run_bash_command


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


def forecaster_fit(expname, var, endleg, yearspan, yearleap):
    """ Function to forecast local temperature using linear fit of output files """

    # get time interval
    endyear = get_year(endleg)
    startyear = get_startyear(endyear, yearspan)

    # get forecast year
    foreyear = get_forecast_year(endyear,yearleap)
    xf = _forecast_xarray(foreyear)

    # load data
    data = reader_nemo(expname, startyear, endyear)

    # fit
    p = data[var].polyfit(dim='time', deg=1, skipna=True)
    yf = xr.polyval(xf, p.polyfit_coefficients)
    yf = yf.rename({'time': 'time_counter', 'z': 'nav_lev'})
    yf = yf.drop_indexes({'x', 'y'})
    yf = yf.reset_coords({'x', 'y'}, drop=True)
    
    rdata = reader_rebuilt(expname, endleg, endleg)
    varlist = ['tn', 'tb']
    for var1 in varlist:
        rdata[var1] = xr.where(rdata[var1] != 0 , yf.values, 0.0)

    return rdata


def forecaster_fit_restart(expname, endleg, yearspan, yearleap):
    """ Function to forecast local temperature using linear fit of restart files """

    # get time interval
    endyear = get_year(endleg)
    startyear = get_startyear(endyear, yearspan)

    # get forecast year
    foreyear = get_forecast_year(endyear,yearleap)
    xf = _forecast_xarray(foreyear)

    # load restarts
    rdata = reader_restart(expname, startyear, endyear)

    # fit
    yf = deepcopy(rdata)
    varlist=['tn', 'tb']
    for variable in varlist:
        p = rdata[variable].polyfit(dim='time_counter', deg=1, skipna=True)
        yf[variable].data = xr.polyval(xf, p.polyfit_coefficients).data
    #yf = yf.rename({'time': 'time_counter', 'z': 'nav_lev'})
    #yf = yf.drop_indexes({'x', 'y'})
    #yf = yf.reset_coords({'x', 'y'}, drop=True)

    #rdata = read_rebuilt(expname, endleg, endleg)
    #for variable in varlist: 
        #yf[var] = yf[var].where( yf < -1.8, rdata[var], yf[var])
    #    rdata[variable] = yf[variable]

    return yf


def forecaster_EOF(expname, var, endleg, yearspan, yearleap):
    """ Function to forecast temperature field using EOF """

    dirs = folders(expname)
    startleg = get_startleg(endleg, yearspan)
    startyear = get_year(startleg)
    endyear = get_year(endleg)
    window = endyear - startyear + 1

    # forecast year
    foreyear = get_forecast_year(endyear, yearleap)
    xf = _forecast_xarray(foreyear)

    # create EOF
    run_cdo_old.merge(expname, startyear, endyear)
    run_cdo_old.selname(expname, var, endleg, 'year')
    run_cdo_old.detrend(expname, var, endleg)
    run_cdo_old.get_EOF(expname, var, endleg, window)
    
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern.nc")
    pattern = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
    field = pattern.isel(time=0)*0
    for i in range(window):
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_series_0000{i}.nc")    
        timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_timeseries_3D)
        p = timeseries.polyfit(dim='time', deg=1, skipna = True)
        theta = xr.polyval(xf, p[f"{var}_polyfit_coefficients"])
        #theta = timeseries[var].isel(time=-1)
        basis = pattern.isel(time=i)
        field = field + theta*basis
    #field = field.drop_vars({'time'})

    # retrend
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}.nc")
    xdata = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
    ave = timemean(xdata, var)
    total = field + ave

    # read forecast and change restart
    rdata = reader_rebuilt(expname, endleg, endleg)
    #total = total.expand_dims({'time': 1})
    total = postproc_var_3D(total)
    total['time_counter'] = rdata['time_counter']
    varlist=['tn', 'tb']
    for vars in varlist:
        rdata[vars] = xr.where(rdata[vars]!=0.0, total[var], 0.0)

    return rdata


def forecaster_EOF_winter(expname, 
                          varname, 
                          endleg, 
                          yearspan, 
                          yearleap, 
                          reco=False):
    """ 
    Function to forecast winter temperature field using EOF 
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: leg 
    yearspan: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    reco: reconstruction of present time
    
    """

    dirs = folders(expname)
    startleg = get_startleg(endleg, yearspan)
    startyear = get_year(startleg)
    endyear = get_year(endleg)
    window = endyear - startyear + 1

    # forecast year
    foreyear = get_forecast_year(endyear, yearleap)
    xf = _forecast_xarray(foreyear)

    # create EOF
    run_cdo_old.merge_winter(expname, varname, startyear, endyear)    
    run_cdo_old.detrend(expname, varname, endleg)
    run_cdo_old.get_EOF(expname, varname, endleg, window)
    
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_pattern.nc")
    pattern = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
    field = pattern.isel(time=0)*0
    for i in range(window):
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_series_0000{i}.nc")    
        timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_timeseries_3D)
        if reco == False:
            p = timeseries.polyfit(dim='time', deg=1, skipna = True)
            theta = xr.polyval(xf, p[f"{varname}_polyfit_coefficients"])
        else:
            theta = timeseries[varname].isel(time=-1)
        basis = pattern.isel(time=i)
        field = field + theta*basis

    if reco ==  False:   
        field = field.drop_vars({'time'})

    # retrend
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
    xdata = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
    ave = timemean(xdata, varname)
    total = field + ave

    # read forecast and change restart
    rdata = reader_rebuilt(expname, endleg, endleg)
    #if reco == False:
    #    total = total.expand_dims({'time': 1})
    total = postproc_var_3D(total)
    total['time_counter'] = rdata['time_counter']
    varlist=['tn', 'tb']
    for vars in varlist: 
        rdata[vars] = xr.where(rdata[vars]!=0.0, total[varname], 0.0)

    return rdata


def forecaster_EOF_restart(expname, 
                           endleg, 
                           yearspan, 
                           yearleap, 
                           reco=False):
    """ 
    Function to forecast temperature fields of restart files using EOF 
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: leg 
    yearspan: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    reco: reconstruction of present time
    
    """

    dirs = folders(expname)
    startleg = get_startleg(endleg, yearspan)
    startyear = get_year(startleg)
    endyear = get_year(endleg)
    window = endyear - startyear + 1

    # forecast year
    #foreyear = get_forecast_year(endyear, yearleap)
    #xf = _forecast_xarray(foreyear)

    # read rebuilt    
    rdata = reader_rebuilt(expname, endleg, endleg)
    #xf = rdata['time_counter'] + yearleap

    # merge and change time axis
    run_cdo_old.merge_rebuilt(expname, startleg, endleg)

    varlist=['tn', 'tb']
    for var in varlist:

        # compute EOF
        run_cdo_old.detrend(expname, var, endleg)
        run_cdo_old.get_EOF(expname, var, endleg, window)
        
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_series_00000.nc")
        timeseries = xr.open_mfdataset(filename)
        xf = timeseries['time_counter'].isel(time_counter=-1)+yearleap

        # project or reconstruct
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern.nc")
        pattern = xr.open_mfdataset(filename)
        field = pattern.isel(time_counter=0)*0        
        for i in range(window-1):
            filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_series_0000{i}.nc")            
            timeseries = xr.open_mfdataset(filename)
            #timeseries = timeseries.squeeze({'zaxis_Reduced', 'lat', 'lon'})
            timeseries = timeseries.isel(lon=0,lat=0,zaxis_Reduced=0)
            timeseries = timeseries.drop_vars({'lon', 'lat', 'zaxis_Reduced'})
            if (reco == False):
                p = timeseries.polyfit(dim='time_counter', deg=1, skipna = True)
                theta = xr.polyval(xf, p[f"{var}_polyfit_coefficients"])
            else:
                theta = timeseries[var].isel(time_counter=-1)
            basis = pattern.isel(time_counter=i)
            field = field + theta*basis
        
        #field = field.squeeze({'zaxis_Reduced', 'lat', 'lon'})
        # add mean to the field
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}.nc")
        xdata = xr.open_mfdataset(filename, use_cftime=True)
        ave = xdata[var].mean(dim=['time_counter'])
        total = field + ave

        # final adjustments
        total = total.expand_dims({'time_counter': 1})  
        total['time_counter'] = rdata['time_counter']
        rdata[var] = total[var]

    return rdata

def forecaster_EOF_winter_multivar(expname, varnames, endleg, yearspan, yearleap, reco=False):
    """ 
    Function to forecast winter temperature field using EOF 
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: leg 
    yearspan: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    reco: reconstruction of present time
    
    """

    dirs = folders(expname)
    startleg = get_startleg(endleg, yearspan)
    startyear = get_year(startleg)
    endyear = get_year(endleg)
    window = endyear - startyear + 1

    # forecast year
    foreyear = get_forecast_year(endyear, yearleap)
    xf = _forecast_xarray(foreyear)

    # read forecast and change restart
    rdata = reader_rebuilt(expname, endleg, endleg)

    # Define the varlists for each variable
    varlists = {
        'thetao': ['tn', 'tb'],
        'so': ['sn', 'sb'],
        'zos': ['sshn', 'sshb']
    }

    # create EOF
    for varname in varnames:
        run_cdo_old.merge_winter(expname, varname, startyear, endyear)    
        run_cdo_old.detrend(expname, varname, endleg)
        run_cdo_old.get_EOF(expname, varname, endleg, window)
    
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_pattern.nc")
        pattern = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
        field = pattern.isel(time=0)*0
        for i in range(window):
            filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_series_0000{i}.nc")    
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_timeseries_3D)
            if reco == False:
                p = timeseries.polyfit(dim='time', deg=1, skipna = True)
                theta = xr.polyval(xf, p[f"{varname}_polyfit_coefficients"])
            else:
                theta = timeseries[varname].isel(time=-1)
            basis = pattern.isel(time=i)
            field = field + theta*basis

        if reco ==  False:   
            field = field.drop_vars({'time'})

        # retrend
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
        xdata = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_pattern_3D)
        ave = timemean(xdata, varname)
        total = field + ave

        #if reco == False:
        #    total = total.expand_dims({'time': 1})
        total = postproc_var_3D(total)
        total['time_counter'] = rdata['time_counter']

        # loop on the corresponding varlist    
        varlist = varlists.get(varname, []) # Get the corresponding varlist, default to an empty list if not found
        for vars in varlist:
            rdata[vars] = xr.where(rdata[vars] != 0.0, total[varname], 0.0)

    return rdata