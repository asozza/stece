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

from osprey.utils import config
from osprey.utils import run_cdo
from osprey.utils import catalogue
from osprey.actions.reader import reader_nemo, reader_rebuilt
from osprey.actions.stabilizer import constraints_for_fields
from osprey.means.eof import project_eofs, process_data
from osprey.utils.time import get_year, get_startyear, get_forecast_year


# Define the varlists for each variable
varlists = {
    'thetao': ['tn', 'tb'],
    'so': ['sn', 'sb'],
    'zos': ['sshn', 'sshb'],
    'uo': ['un', 'ub'],
    'vo': ['vn', 'vb']
}


###########################################################################################################

def forecaster_EOF_def(expname, varnames, endleg, yearspan, yearleap, mode='full', smoothing=False, debug=False):
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
        
        field = create_forecast_field(expname, varname, endleg, yearspan, yearleap, mode='full', smoothing=False, debug=debug)

        field = field.rename({'time': 'time_counter', 'z': 'nav_lev'})
        field['time_counter'] = rdata['time_counter']

        # loop on the corresponding varlist    
        varlist = varlists.get(varname, []) # Get the corresponding varlist, default to an empty list if not found
        for vars in varlist:
            rdata[vars] = xr.where(rdata[vars] != 0.0, field[varname], 0.0)

    return rdata


def create_forecast_field(expname, varname, endleg, yearspan, yearleap, mode='full', format='winter', smoothing=False, debug=False):
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
    dirs = config.folders(expname)

    # prepare field and EOFs
    # ISSUE: run_cdo COMMANDS can be replaced by xrarray operations
    run_cdo.merge(expname, varname, startyear, endyear, format=format, grid=info['grid'])
    run_cdo.detrend(expname, varname, endleg)
    run_cdo.get_eofs(expname, varname, endleg, window)
    
    # field projection in the future
    data = project_eofs(expname=expname, varname=varname, endleg=endleg, yearspan=yearspan, yearleap=yearleap, mode=mode, debug=debug)
    
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


