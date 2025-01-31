#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Forecasters Module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: Mar 2024
"""

import os
import yaml
import numpy as np
import logging
import xarray as xr

from osprey.utils import config
from osprey.utils import run_cdo
from osprey.utils import catalogue

from osprey.actions.reader import reader_rebuilt
from osprey.actions.reader import reader_nemo_field
from osprey.actions.stabilizer import constraints_for_fields
from osprey.means.eof import project_eofs, process_data 
from osprey.means.eof import reader_EOF_coeffs, performance_eofs, mean_performance_eofs
from osprey.means.means import spacemean
from osprey.utils.time import get_decimal_year

# Define the varlists for each variable
varlists = {
    'thetao': ['tn', 'tb'],
    'so': ['sn', 'sb'],
    'zos': ['sshn', 'sshb'],
    'uo': ['un', 'ub'],
    'vo': ['vn', 'vb']
}

###########################################################################################################

def create_forecast_field(expname, varname, endleg, window, yearleap, mode='full', format='winter', smoothing=False, debug=False):
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

    startleg = endleg - window + 1
    startyear = 1990 + startleg - 2
    endyear = 1990 + endleg - 2

    logging.info(f"Start/end year: {startyear}-{endyear}")
    logging.info(f"Time window: {window}")

    info = catalogue.observables('nemo')[varname]
    dirs = config.folders(expname)
    dirs['tmp'] = os.path.join(dirs['tmp'], )

    # prepare field and EOFs
    # ISSUE: run_cdo COMMANDS can be replaced by xrarray operations
    run_cdo.pymerge(expname, varname, startyear, endyear, format=format, grid=info['grid'])
    run_cdo.detrend(expname, varname, endleg)
    run_cdo.get_eofs(expname, varname, endleg, window)
    
    # field projection in the future
    data = project_eofs(expname=expname, varname=varname, endleg=endleg, window=window, yearleap=yearleap, mode=mode, debug=debug)
    
    # apply constraints
    data = constraints_for_fields(data=data)

    # add smoothing and post-processing features
    if smoothing:
        infile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_total.nc")
        total.to_netcdf(infile, mode='w', unlimited_dims={'time': True})
        outfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_smoother.nc")
        run_cdo.add_smoothing(infile, outfile)
        total = xr.open_mfdataset(outfile, use_cftime=True, preprocess=lambda data: process_data(data, ftype='post', dim=info['dim'], grid=info['grid']))

    return data

###########################################################################################################


def forecaster_EOF_def(expname, varnames, endleg, window, yearleap, mode='full', smoothing=False, debug=False):
    """ 
    Function to assembly the forecast of multiple fields using EOF
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: final leg of the simulation
    window: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    mode: EOF regression mode
    smoothing: if needed, smooth out the forecasted fields
    
    """

    # read forecast and change restart
    rdata = reader_rebuilt(expname, endleg, endleg)

    # create EOF
    for varname in varnames:
        
        field = create_forecast_field(expname, varname, endleg, window, yearleap, mode='full', smoothing=False, debug=debug)

        field = field.rename({'time': 'time_counter', 'z': 'nav_lev'})
        field['time_counter'] = rdata['time_counter']

        # loop on the corresponding varlist    
        varlist = varlists.get(varname, []) # Get the corresponding varlist, default to an empty list if not found
        for vars in varlist:
            rdata[vars] = xr.where(rdata[vars] != 0.0, field[varname], 0.0)

    return rdata

###########################################################################################################


def collect_performance_data(expname, varname, endleg, window, yearleap, mode='full', smoothing=False, debug=False):
    """ 
    Function to test the EOF forecaster
    
    Args:
    expname: experiment name
    varname: variable name
    endleg: final leg of the simulation
    yearspan: years backward from endleg used by EOFs
    yearleap: years forward from endleg to forecast
    mode: EOF regression mode
    smoothing: if needed, smooth out the forecasted fields
    
    """
    
    startleg = endleg - window + 1
    startyear = 1990 + startleg - 2
    endyear = 1990 + endleg - 2
    targetyear = endyear + yearleap

    logging.info(f"Start/end year: {startyear}-{endyear}")
    logging.info(f"Time window: {window}")

    # load variable info
    info = catalogue.observables('nemo')[varname]
    
    # create forecast field
    fdata = create_forecast_field(expname=expname, varname=varname, endleg=endleg, window=window, yearleap=yearleap, mode='full', smoothing=False, debug=debug)

    # read the unperturbed field (check time window foreyear+1)
    udata = reader_nemo_field(expname=expname, startyear=startyear, endyear=targetyear, varname=varname)

    # read EOF timeseries
    eof_slope, eof_intercept = reader_EOF_coeffs(expname, endleg, varname)

    # dry-run analysis
    delta, squared_delta, slope = performance_eofs(fdata, udata, targetyear, varname)
    mean_delta, mean_squared_delta, mean_slope = mean_performance_eofs(delta, squared_delta, slope, info)

    pdata = xr.Dataset(
        {
            "mean_delta": (["endleg", "window", "yearleap"], [[[mean_delta.values.flatten()[0]]]]),
            "mean_squared_delta": (["endleg", "window", "yearleap"], [[[mean_squared_delta.values.flatten()[0]]]]),
            "mean_slope": (["endleg", "window", "yearleap"], [[[mean_slope.values.flatten()[0]]]]),
            "eof_slope": (["endleg", "window", "yearleap"], [[[eof_slope]]]), 
        },
        coords={
            "endleg": [endleg],
            "window": [window],
            "yearleap": [yearleap],
        },
    )

    pdata.to_netcdf(f"{expname}_{varname}_{endleg}_{window}_{yearleap}.nc")

    return pdata

###########################################################################################################

def dryrunner(expname, varname, mode='full', smoothing=False, debug=False):
    """ Dry runner for the forecaster, looping over parameters: endleg, window, yearleap """

    def run_collect_performance_data(params):
        expname, varname, endleg, window, yearleap, mode, smoothing, debug = params
        if endleg > window:
            return collect_performance_data(expname, varname, endleg, window, yearleap, mode, smoothing, debug)
        else:
            logging.info(f"Skipping: {endleg} < {window}")

    # Load parameter ranges from a YAML file
    with open('params.yaml', 'r') as file:
        params = yaml.safe_load(file)

    # Extract ranges from the loaded parameters
    window_range = params['window']
    yearleap_range = params['yearleap']
    endleg_range = params['endleg']

    # create a list of parameters for each function call
    params_list = [
        (expname, varname, endleg, window, yearleap, mode, smoothing, debug)
        for window in window_range
        for yearleap in yearleap_range
        for endleg in endleg_range
    ]

    #pdata = xr.Dataset()
    for params in params_list:
        ds = run_collect_performance_data(params)
        #if ds is not None:
        #    datasets.append(ds)
        #pdata = xr.merge([pdata, ds])

    #pdata = xr.concat(datasets, dim=["endleg", "window", "yearleap"])

    return None 
