#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forecasters Module

Author: Alessandro Sozza (CNR-ISAC)
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
from osprey.actions.post_reader import reader_restart
from osprey.means.eof import save_EOF
from osprey.means.eof import preproc_pattern_2D, preproc_pattern_3D, preproc_timeseries_2D, preproc_timeseries_3D, preproc_forecast_3D
from osprey.utils import cdo

def _forecast_xarray(foreyear):
    """Get the xarray for the forecast time"""
    
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 0, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])},
                      attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    return xf


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
        rdata[var1] = xr.where(rdata[var1] !=0, yf.values, 0.0)

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

# add vfrac: percetuage of EOF to consider: 1.0 -> all
def forecaster_EOF(expname, var, ndim, endleg, yearspan, yearleap):
    """ Function to forecast temperature field using EOF """

    dirs = folders(expname)
    startleg = get_startleg(endleg, yearspan)
    startyear = get_year(startleg)
    endyear = get_year(endleg)
    window = endyear - startyear

    # forecast year
    foreyear = get_forecast_year(endyear, yearleap)
    xf = _forecast_xarray(foreyear)

    # create EOF
    cdo.merge(expname, startyear, endyear)
    cdo.selname(expname, startyear, endyear, var)
    cdo.detrend(expname, startyear, endyear, var)
    cdo.get_EOF(expname, startyear, endyear, var, ndim)
    
    if ndim == '2D':
        pattern = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc"),
                                    use_cftime=True, preprocess=preproc_pattern_2D)
    if ndim == '3D':
        pattern = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc"),
                                    use_cftime=True, preprocess=preproc_pattern_3D)
    field = pattern.isel(time=0)*0

    for i in range(window):      
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_timeseries_{startyear}-{endyear}_0000{i}.nc")
        if ndim == '2D':
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_timeseries_2D)
        if ndim == '3D':
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_timeseries_3D)
        p = timeseries.polyfit(dim='time', deg=1, skipna = True)
        theta = xr.polyval(xf, p[f"{var}_polyfit_coefficients"])
        laststep = pattern.isel(time=i)
        field = field + theta.isel(time=0,lat=0,lon=0)*laststep

    # save EOF
    save_EOF(expname, startyear, endyear, field, var, ndim)

    # add trend
    cdo.retrend(expname, startyear, endyear, var)

    # read forecast and change restart
    data = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast_{startyear}-{endyear}.nc"),
                             use_cftime=True, preprocess=preproc_forecast_3D)
    rdata = reader_rebuilt(expname, endleg, endleg)
    data['time_counter'] = rdata['time_counter']
    varlist = ['tn', 'tb']
    for var1 in varlist:
        rdata[var1] = data[var]

    return rdata


def forecaster_EOFS(expname, endleg, yearspan, yearleap):
    """ Function to forecast temperature field using EOF, producing the same field """

    dirs = folders(expname)
    startleg = get_startleg(endleg, yearspan)
    startyear = get_year(startleg)
    endyear = get_year(endleg)
    window = endyear - startyear

    # forecast year
    foreyear = get_forecast_year(endyear, yearleap)
    xf = _forecast_xarray(foreyear)

    # create EOF
    var='thetao'
    ndim='3D'
    cdo.merge(expname, startyear, endyear)
    cdo.selname(expname, startyear, endyear, var)
    cdo.detrend(expname, startyear, endyear, var)
    cdo.get_EOF(expname, startyear, endyear, var, ndim)

    pattern = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc"),
                                    use_cftime=True, preprocess=preproc_pattern_3D)
    field = pattern.isel(time=0)*0

    for i in range(window):
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_timeseries_{startyear}-{endyear}_0000{i}.nc")
        timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=preproc_timeseries_3D)
        p = timeseries.polyfit(dim='time', deg=1, skipna = True)
        theta = xr.polyval(timeseries['time'].isel(time=-1), p[f"{var}_polyfit_coefficients"])
        laststep = pattern.isel(time=i)
        field = field + theta.isel(lat=0,lon=0)*laststep

    # save EOF
    save_EOF(expname, startyear, endyear, field, var, ndim)

    # add trend
    cdo.retrend(expname, startyear, endyear, var)

    # read forecast and change restart
    data = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast_{startyear}-{endyear}.nc"),
                             use_cftime=True, preprocess=preproc_forecast_3D)
    rdata = reader_rebuilt(expname, endleg, endleg)
    data['time_counter'] = rdata['time_counter']
    varlist = ['tn', 'tb']
    for var1 in varlist:
        rdata[var1] = data[var]

    return rdata