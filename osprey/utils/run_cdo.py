#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CDO module

Author: Alessandro Sozza (CNR-ISAC) 
Date: June 2024
"""

import os
import glob
import numpy as np
import logging
import xarray as xr
from cdo import Cdo

from osprey.utils import config
from osprey.utils import catalogue

from osprey.utils.utils import error_handling_decorator, remove_existing_file, remove_existing_filelist
from osprey.utils.time import get_leg, get_season_months

# Initialize CDO
cdo = Cdo()

@error_handling_decorator
def cat(expname, startyear, endyear, grid='T', freq='1m'):
    """ CDO command to merge files """

    dirs = config.folders(expname)
    leg = get_leg(endyear+1)

    filelist = []
    for year in range(startyear, endyear+1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_{freq}_{grid}_{year}-{year}.nc")
        print(pattern)
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)
    datafile = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")
    remove_existing_file(datafile)
    
    cdo.run(f"cat {' '.join(filelist)} {datafile}")

    return None


@error_handling_decorator
def selname(expname, varname, leg, cleanup=True):
    """ CDO command to select variable """

    dirs = config.folders(expname)

    datafile = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")

    varfile = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{varname}.nc")
    remove_existing_file(varfile)
    
    cdo.run(f"selname,{varname} {datafile} {varfile}")      

    if cleanup:
        remove_existing_file(datafile)

    return None


@error_handling_decorator
def timmean(expname, varname, leg, format='global'):
    """ CDO command to compute time mean """

    dirs = config.folders(expname)

    infile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")

    outfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_timmean.nc")
    remove_existing_file(outfile)

    if format == 'global':
        cdo.run(f"timmean {infile} {outfile}")

    elif format == 'seasonal' or format in get_season_months():
        cdo.run(f"seasmean {infile} {outfile}")

        if format in get_season_months():
            cdo.run(f"selmon,{get_season_months()[format][1]} {infile} {outfile}")

    return None


@error_handling_decorator
def merge(expname, varname, startyear, endyear, format='winter', grid='T', freq='1m'):
    """ CDO command to merge data """

    dirs = config.folders(expname)
    endleg = endyear - 1990 + 2
    
    os.makedirs(os.path.join(dirs['tmp'], str(endleg).zfill(3)), exist_ok=True)

    cat(expname=expname, startyear=startyear, endyear=endyear, grid=grid, freq=freq)
    selname(expname=expname, varname=varname, leg=endleg)
    timmean(expname=expname, varname=varname, leg=endleg, format=format)

    # rename final file
    old_file = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}_timmean.nc")
    new_file = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
    if os.path.exists(old_file):
        os.rename(old_file, new_file)

    return None


@error_handling_decorator
def detrend(expname, varname, leg):
    """Detrend data by subtracting the time average using the CDO Python package."""
    
    dirs = config.folders(expname)

    varfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")

    anomfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    remove_existing_file(anomfile)

    logging.info(f"Detrending variable {varname} by subtracting the time average.")
    
    cdo.sub(input=[varfile, f"-timmean {varfile}"], output=anomfile)

    return None


@error_handling_decorator
def retrend(expname, varname, leg):
    """Add trend to a variable using the CDO Python package with error handling."""

    # Get the directories and file paths
    dirs = config.folders(expname)
    
    # Define file paths for the original data, auxiliary product, and the final forecast
    inifile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")
    auxfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_eof.nc")
    updfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_eof_updated.nc")
    newfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_proj.nc")
    
    # Remove existing forecast file if it already exists
    remove_existing_file(newfile)

    logging.info(f"Adding time and depth bounds to {varname} using {inifile} in {auxfile}.")
    cdo.run(f"selvar,time_counter_bnds,deptht_bnds {inifile} time_depth_bnds.nc")
    cdo.run(f"merge {auxfile} time_depth_bnds.nc {updfile}")

    logging.info(f"Adding trend to {varname} using {inifile} on {auxfile}.")
    
    # CDO command to add the trend back to the detrended data
    cdo.add(input=[auxfile, f"-timmean {inifile}"], output=newfile)

    logging.info(f"Retrended forecast data created: {newfile}")

    return None


@error_handling_decorator
def get_eofs(expname, varname, leg, window):
    """Compute EOF using the CDO Python package with error handling."""
    
    # Get the directories and file paths
    dirs = config.folders(expname)
    info = catalogue.observables('nemo')[varname]

    # Define file paths for anomaly, covariance, and pattern output files
    flda = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_variance.nc")
    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_pattern.nc")
    
    # Remove existing output files if they already exist
    remove_existing_file(fldcov)
    remove_existing_file(fldpat)

    logging.info(f"Computing EOFs for variable {varname} with window size {window}.")
    
    # CDO command to compute EOFs covariance and pattern
    if info['dim'] == '3D':
        logging.info(f"Compute 3D EOFs")
        cdo.run(f"eof3d,{window} {flda} {fldcov} {fldpat}")
    elif info['dim'] == '2D':   
        logging.info(f"Compute 2D EOFs")        
        cdo.run(f"eof,{window} {flda} {fldcov} {fldpat}")

    # Define timeseries output file pattern
    timeseries = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_series_")
    remove_existing_filelist(timeseries)

    # Compute EOF coefficients (timeseries)
    logging.info(f"Computing EOF coefficients for {varname}.")
    if info['dim'] == '3D':
        cdo.run(f"eofcoeff3d {fldpat} {flda} {timeseries}")
    elif info['dim'] == '2D':
        cdo.run(f"eofcoeff {fldpat} {flda} {timeseries}")

    logging.info(f"EOF computation completed successfully: {fldcov}, {fldpat}, {timeseries}")
    
    return None


@error_handling_decorator
def EOF_info(expname, varname, leg):
    """Get the relative magnitude of EOF eigenvectors using the CDO Python package with error handling."""

    # Get the directories and file path for the covariance (variance) file
    dirs = config.folders(expname)
    cov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_variance.nc")

    logging.info(f"Getting relative magnitude of EOF eigenvectors for {varname} using {cov}")

    # CDO command to get relative magnitude (eigenvalues info) of the EOF eigenvectors
    cdo.info(input=f"-div {cov} -timsum {cov}")

    logging.info(f"Relative magnitude of EOF eigenvectors for {varname} computed successfully")

    return None


@error_handling_decorator
def add_smoothing(input, output):
    """ add smoothing """

    remove_existing_file(output)

    cdo.smooth("radius=10deg", input=input, output=output)
    #cdo.smooth9(input=input, output=output)

    return None

