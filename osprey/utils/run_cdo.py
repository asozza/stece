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

from osprey.utils.folders import folders
from osprey.utils.utils import run_bash_command
from osprey.utils.utils import error_handling_decorator, remove_existing_file, remove_existing_filelist
from osprey.utils.time import get_leg, get_year
from osprey.utils import catalogue
from osprey.actions.reader import reader_nemo

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize CDO
cdo = Cdo()

@error_handling_decorator
def merge_winter(expname, varname, startyear, endyear, grid='T'):
    """ CDO command to merge winter-only data """

    dirs = folders(expname)
    endleg = endyear - 1990 + 2
    
    os.makedirs(os.path.join(dirs['tmp'], str(endleg).zfill(3)), exist_ok=True)

    for year in range(startyear-1, endyear):
        filelist = []
        for i in range(2):
            pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_{grid}_{year-i}-{year-i}.nc")
            matching_files = glob.glob(pattern)
            filelist.extend(matching_files)

        datafile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_data.nc")
        remove_existing_file(datafile)
        varfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_monthly.nc")
        remove_existing_file(varfile)
        djfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_DJ.nc")
        remove_existing_file(djfile)
        auxfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_DJ2.nc")
        remove_existing_file(auxfile)
        winterfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_winter_{year}.nc")
        remove_existing_file(winterfile)

        cdo.run(f"cat {' '.join(filelist)} {datafile}")        
        cdo.run(f"selname,{varname} {datafile} {varfile}")        
        cdo.run(f"selmon,12,1 {varfile} {djfile}")        
        cdo.run(f"delete,timestep=1,-1 {djfile} {auxfile}")        
        cdo.run(f"timmean {auxfile} {winterfile}")

    filelist = []
    for year in range(startyear-1, endyear):
        pattern = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_winter_{year}.nc")                        
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)

    datafile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{varname}.nc")
    remove_existing_file(datafile)

    cdo.run(f"cat {' '.join(filelist)} {datafile}")

    auxfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_")
    remove_existing_filelist(auxfile)

    return None


@error_handling_decorator
def detrend(expname, varname, leg):
    """Detrend data by subtracting the time average using the CDO Python package."""
    
    dirs = folders(expname)
    varfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")
    anomfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    remove_existing_file(anomfile)

    logging.info(f"Detrending variable {varname} by subtracting the time average.")
    
    # Detrending using CDO: subtract the time mean from the variable
    cdo.sub(input=[varfile, f"-timmean {varfile}"], output=anomfile)

    return None


@error_handling_decorator
def get_EOF(expname, varname, leg, window):
    """Compute EOF using the CDO Python package with error handling."""

    # Get the directories and file paths
    dirs = folders(expname)
    info = catalogue.observables('nemo')[varname]

    # Define file paths for anomaly, covariance, and pattern output files
    flda = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_variance.nc")
    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_pattern.nc")
    
    # Remove existing output files if they already exist
    remove_existing_file(fldcov)
    remove_existing_file(fldpat)

    logging.info(f"Computing EOF for variable {varname} with window size {window}.")
    
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
def retrend(expname, varname, leg):
    """Add trend to a variable using the CDO Python package with error handling."""

    # Get the directories and file paths
    dirs = folders(expname)
    
    # Define file paths for the original data, auxiliary product, and the final forecast
    inifile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")
    auxfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_product.nc")
    newfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_forecast.nc")
    
    # Remove existing forecast file if it already exists
    remove_existing_file(newfile)

    logging.info(f"Adding trend to {varname} using {auxfile} and {inifile}.")

    # CDO command to add the trend back to the detrended data
    cdo.add(input=[auxfile, f"-timmean {inifile}"], output=newfile)

    logging.info(f"Retrended forecast data created: {newfile}")

    return None


@error_handling_decorator
def EOF_info(expname, varname, leg):
    """Get the relative magnitude of EOF eigenvectors using the CDO Python package with error handling."""

    # Get the directories and file path for the covariance (variance) file
    dirs = folders(expname)
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

    #cdo.smooth("radius=2deg", input=input, output=output)
    cdo.smooth9(input=input, output=output)

    return None

