#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forecasters Module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: Mar 2024
"""

import os
import numpy as np
import cftime
import logging
import shutil
import xarray as xr

from osprey.actions.reader import reader_nemo, reader_rebuilt
from osprey.actions.stabilizer import constraints_for_restart, constraints_for_fields
from osprey.means.eof import project_eofs, process_data
from osprey.means.means import timemean
from osprey.utils.folders import folders
from osprey.utils.time import get_year, get_startyear, get_forecast_year
from osprey.utils import run_cdo
from osprey.utils import catalogue


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the varlists for each variable
varlists = {
    'thetao': ['tn', 'tb'],
    'so': ['sn', 'sb'],
    'zos': ['sshn', 'sshb'],
    'uo': ['un', 'ub'],
    'vo': ['vn', 'vb']
}


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
    Function to assembly the forecast of multiple fields using EOF
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: final leg of the simulation
    yearspan: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    mode: EOF regression mode
    smoothing: if needed, smooth out the forecasted fields
    
    """

    # read forecast and change restart
    rdata = reader_rebuilt(expname, endleg, endleg) 

    # create EOF
    for varname in varnames:
        
        field = create_forecast_field(expname, varname, endleg, yearspan, yearleap, mode='full', smoothing=False)

        field = field.rename({'time': 'time_counter', 'z': 'nav_lev'})
        field['time_counter'] = rdata['time_counter']

        # loop on the corresponding varlist    
        varlist = varlists.get(varname, []) # Get the corresponding varlist, default to an empty list if not found
        for vars in varlist:
            rdata[vars] = xr.where(rdata[vars] != 0.0, field[varname], 0.0)

    return rdata


def create_forecast_field(expname, varname, endleg, yearspan, yearleap, mode='full', format='winter', smoothing=False):
    """ 
    Function to forecast a single field using EOF
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: final leg of the simulation
    yearspan: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    mode: EOF regression mode
    format: time format [plain, moving, winter, etc ...]
    smoothing: if needed, smooth out the forecasted fields
    
    """


    startleg = endleg - yearspan + 1
    startyear = 1990 + startleg - 2
    endyear = 1990 + endleg - 2
    window = endyear - startyear + 1

    logging.info(f"Start/end year: {startyear}-{endyear}")
    logging.info(f"Time window: {window}")

    info = catalogue.observables('nemo')[varname]
    dirs = folders(expname)

    # forecast year
    foreyear = get_forecast_year(endyear, yearleap)
    xf = _forecast_xarray(foreyear)

    # prepare field and EOFs
    # ISSUE: run_cdo COMMANDS can be replaced by xrarray operations
    run_cdo.merge(expname, varname, startyear, endyear, format=format, grid=info['grid'])
    run_cdo.detrend(expname, varname, endleg)
    run_cdo.get_EOF(expname, varname, endleg, window)

    # field projection in the future
    field = project_eofs(expname=expname, varname=varname, endleg=endleg, neofs=window, xf=xf, mode=mode)
     
    # retrend
    filename = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
    xdata = xr.open_mfdataset(filename, use_cftime=True, preprocess=lambda data: process_data(data, ftype='pattern', dim=info['dim'], grid=info['grid']))
    ave = timemean(xdata[varname])
    total = field + ave
    if info['dim'] == '3D':
        total = total.transpose("time", "z", "y", "x")
    if info['dim'] == '2D':
        total = total.transpose("time", "y", "x")

    # move constraints here, before smoothing.
    total = constraints_for_fields(total)

    # add smoothing and post-processing features
    if smoothing:
        infile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_total.nc")
        total.to_netcdf(infile, mode='w', unlimited_dims={'time': True})
        outfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_smoother.nc")
        run_cdo.add_smoothing(infile, outfile)
        total = xr.open_mfdataset(outfile, use_cftime=True, preprocess=lambda data: process_data(data, ftype='post', dim=info['dim'], grid=info['grid']))    

    return total



###########################################################################################################

