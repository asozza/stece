#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forecasters Module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: Mar 2024
"""

import os
import subprocess
import numpy as np
import cftime
import logging
import shutil
import xarray as xr

from osprey.actions.reader import reader_nemo, reader_rebuilt 
from osprey.actions.stabilizer import constraints
from osprey.means.eof import project_eofs, process_data
from osprey.means.means import timemean
from osprey.utils.folders import folders
from osprey.utils.time import get_year, get_startyear, get_forecast_year
from osprey.utils import run_cdo
from osprey.utils import catalogue


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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


###########################################################################################################

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


###########################################################################################################

def forecaster_EOF_def(expname, varnames, endleg, yearspan, yearleap, mode='full', smoothing=False):
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
    startleg = endleg - yearspan + 1
    startyear = 1990 + startleg - 2
    endyear = 1990 + endleg - 2
    window = endyear - startyear + 1

    logging.info(f"Start/end year: {startyear}-{endyear}")
    logging.info(f"Time window: {window}")

    # forecast year
    foreyear = get_forecast_year(endyear, yearleap)
    xf = _forecast_xarray(foreyear)

    # read forecast and change restart
    rdata = reader_rebuilt(expname, endleg, endleg)

    # Define the varlists for each variable
    varlists = {
        'thetao': ['tn', 'tb'],
        'so': ['sn', 'sb'],
        'zos': ['sshn', 'sshb'],
        'uo': ['un', 'ub'],
        'vo': ['vn', 'vb']
    }

    # create EOF
    for varname in varnames:

        info = catalogue.observables('nemo')[varname]

        # ISSUE: run_cdo COMMANDS can be replaced by xrarray operations
        run_cdo.merge_winter(expname, varname, startyear, endyear, grid=info['grid'])

        # 
        run_cdo.detrend(expname, varname, endleg)

        # add smoothing in pre-processing
        if smoothing:
            infile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_anomaly.nc")
            outfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_anomaly_smoothed.nc")
            run_cdo.add_smoothing(infile, outfile)

            original_file = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_anomaly_original.nc")   
            shutil.copy(infile, original_file)  
            shutil.copy(outfile, infile) 

        #run_cdo_old.get_EOF(expname, varname, endleg, window)
        run_cdo.get_EOF(expname, varname, endleg, window)

        dir = os.path.join(os.path.join(dirs['tmp'], str(endleg).zfill(3)))
        field = project_eofs(dir=dir, varname=varname, neofs=window, xf=xf, mode=mode)
 
        if mode == 'reco':   
            field = field.drop_vars({'time'})

        # retrend
        filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
        xdata = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, mode='pattern', dim=info['dim'], grid=info['grid']))
        ave = timemean(xdata[varname])
        total = field + ave
        if info['dim'] == '3D':
            total = total.transpose("time", "z", "y", "x")
        if info['dim'] == '2D':
            total = total.transpose("time", "y", "x")
        #total = total.expand_dims({'time': 1})

        # add smoothing and post-processing features
        if smoothing:
            infile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_total.nc")
            total.to_netcdf(infile, mode='w', unlimited_dims={'time': True})
            outfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_smoother.nc")
            run_cdo.add_smoothing(infile, outfile)
            total = xr.open_mfdataset(outfile, use_cftime=True, preprocess=lambda data: process_data(data, mode='post', dim=info['dim'], grid=info['grid']))    

        #total = total.rename({'time': 'time_counter', 'z': 'nav_lev'})
        total['time_counter'] = rdata['time_counter']

        # loop on the corresponding varlist    
        varlist = varlists.get(varname, []) # Get the corresponding varlist, default to an empty list if not found
        for vars in varlist:
            rdata[vars] = xr.where(rdata[vars] != 0.0, total[varname], 0.0)
        
        # add constraints
        rdata = constraints(rdata)

    return rdata


###########################################################################################################

