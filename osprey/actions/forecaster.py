#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forecasters Module

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import subprocess
import numpy as np
import os
import glob
import shutil
import yaml
import dask
import cftime
import nc_time_axis
import xarray as xr
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta

import osprey_io as osi
import osprey_means as osm
import osprey_tools as ost
import osprey.actions.checks as osc
import osprey_eof as ose


def forecaster_fit(expname, var, endleg, yearspan, yearleap):
    """ Function to forecast local temperature using linear fit of output files """

    # get time interval
    endyear = ost.get_year(endleg)
    startleg = ost.get_startleg(endleg, yearspan)
    startyear = ost.get_startyear(endyear, yearspan)

    # get forecast year
    foreyear = ost.get_forecast_year(endyear,yearleap)
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 12, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])}, attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    # load data
    data = osi.read_T(expname, startyear, endyear)

    # fit
    p = data[var].polyfit(dim='time', deg=1, skipna=True)
    yf = xr.polyval(xf, p.polyfit_coefficients)
    yf = yf.rename({'time': 'time_counter', 'z': 'nav_lev'})
    yf = yf.drop_indexes({'x', 'y'})
    yf = yf.reset_coords({'x', 'y'}, drop=True)
    
    rdata = osi.read_rebuilt(expname, endleg, endleg)
    varlist = ['tn', 'tb']
    for var1 in varlist:
        rdata[var1] = xr.where(rdata[var1] !=0, yf.values, 0.0)

    return rdata


def forecaster_fit_re(expname, var, endleg, yearspan, yearleap):
    """ Function to forecast local temperature using linear fit of restart files """

    # get time interval
    endyear = ost.get_year(endleg)
    startleg = ost.get_startleg(endleg, yearspan)
    startyear = ost.get_startyear(endyear, yearspan)

    # get forecast year
    foreyear = ost.get_forecast_year(endyear,yearleap)
    fdate = cftime.DatetimeGregorian(foreyear, 1, 1, 12, 0, 0, has_year_zero=False)
    xf = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])}, attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    # load restarts
    rdata = osi.read_restart(expname, startyear, endyear)

    # fit
    yf = {}
    varlist = ['tn', 'tb']
    for vars in varlist:   
        p = rdata[var].polyfit(dim='time', deg=1, skipna=True)
        yf[vars] = xr.polyval(xf, p.polyfit_coefficients)
    yf = yf.rename({'time': 'time_counter', 'z': 'nav_lev'})
    yf = yf.drop_indexes({'x', 'y'})
    yf = yf.reset_coords({'x', 'y'}, drop=True)

    rdata = osi.read_rebuilt(expname, endleg, endleg)
    for vars in varlist: 
        #yf[var] = yf[var].where( yf < -1.8, rdata[var], yf[var])
        rdata[vars] = yf[vars]

    return rdata

# add vfrac: percetuage of EOF to consider: 1.0 -> all
def forecaster_EOF(expname, var, ndim, endleg, yearspan, yearleap):
    """ Function to forecast temperature field using EOF """

    dirs = osi.folders(expname)
    startleg = ost.get_startleg(endleg, yearspan)
    startyear = ost.get_year(startleg)
    endyear = ost.get_year(endleg)
    window = endyear - startyear

    # forecast year
    foreyear = ost.get_forecast_year(endyear, yearleap)
    fdate = cftime.DatetimeGregorian(foreyear, 7, 1, 12, 0, 0, has_year_zero=False)
    foredate = xr.DataArray(data = np.array([fdate]), dims = ['time'], coords = {'time': np.array([fdate])}, attrs = {'stardand_name': 'time', 'long_name': 'Time axis', 'bounds': 'time_counter_bnds', 'axis': 'T'})

    # create EOF
    ose.cdo_merge(expname, startyear, endyear)
    ose.cdo_selname(expname, startyear, endyear, var)
    ose.cdo_detrend(expname, startyear, endyear, var)
    ose.cdo_EOF(expname, startyear, endyear, var, ndim)
    
    if ndim == '2D':
        pattern = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc"), use_cftime=True, preprocess=ose.preproc_pattern_2D)
    if ndim == '3D':
        pattern = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc"), use_cftime=True, preprocess=ose.preproc_pattern_3D)
    field = pattern.isel(time=0)*0

    for i in range(window):        
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_timeseries_{startyear}-{endyear}_0000{i}.nc")
        if ndim == '2D':
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=ose.preproc_timeseries_2D)        
        if ndim == '3D':
            timeseries = xr.open_mfdataset(filename, use_cftime=True, preprocess=ose.preproc_timeseries_3D)        
        p = timeseries.polyfit(dim='time', deg=1, skipna = True)
        theta = xr.polyval(foredate, p[f"{var}_polyfit_coefficients"])
        laststep = pattern.isel(time=i)
        field = field + theta.isel(time=0,lat=0,lon=0)*laststep

    # save EOF
    ose.save_EOF(expname, startyear, endyear, field, var, ndim)

    # add trend
    ose.add_trend_EOF(expname, startyear, endyear, var)

    # read forecast and change restart
    data = xr.open_mfdataset(os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast_{startyear}-{endyear}.nc"), use_cftime=True, preprocess=ose.preproc_forecast_3D) 
    rdata = osi.read_rebuilt(expname, endleg, endleg)
    data['time_counter'] = rdata['time_counter']
    varlist = ['tn', 'tb']
    for var1 in varlist:
        rdata[var1] = data[var]

    return rdata
