#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CDO module

Author: Alessandro Sozza (CNR-ISAC) 
Date: June 2024
"""

import os
import glob
import logging
from cdo import Cdo

from osprey.utils.folders import folders
from osprey.utils.utils import run_bash_command
from osprey.utils.utils import error_handling_decorator, remove_existing_file, remove_existing_filelist
from osprey.utils.time import get_leg, get_year

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize CDO
cdo = Cdo()


@error_handling_decorator
def merge(expname, startyear, endyear):
    """Merge files using the CDO Python package with error handling."""

    dirs = folders(expname)
    leg = get_leg(endyear)

    filelist = []
    for year in range(startyear-2, endyear+1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        logger.info(f"Looking for files matching pattern: {pattern}")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)

    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)
    merged_file = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")
    remove_existing_file(merged_file)

    if filelist:
        logger.info(f"Merging files: {filelist}")
        cdo.cat(input=' '.join(filelist), output=merged_file)
    else:
        logger.error(f"No files found to merge for years {startyear-2} to {endyear+1}")

    return None


@error_handling_decorator
def selname(expname, varname, leg, interval):
    """Select variable and calculate seasonal or yearly means using the CDO Python package."""

    dirs = folders(expname)
    merged_file = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")
    varfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")
    remove_existing_file(varfile)

    if interval == 'year':
        logger.info(f"Selecting yearly mean for variable {varname}")
        cdo.yearmean(input=f"-selname,{varname} {merged_file}", output=varfile)
    
    elif interval == 'winter':
        logger.info(f"Selecting winter months (Dec, Jan, Feb) mean for variable {varname}")
        cdo.timmean(input=f"-selmon,12,1,2 -selname,{varname} {merged_file}", output=varfile)
    
    elif interval == 'spring':
        logger.info(f"Selecting spring months (Mar, Apr, May) mean for variable {varname}")
        cdo.timmean(input=f"-selmon,3,4,5 -selname,{varname} {merged_file}", output=varfile)
    
    elif interval == 'summer':
        logger.info(f"Selecting summer months (Jun, Jul, Aug) mean for variable {varname}")
        cdo.timmean(input=f"-selmon,6,7,8 -selname,{varname} {merged_file}", output=varfile)
    
    elif interval == 'fall':
        logger.info(f"Selecting fall months (Sep, Oct, Nov) mean for variable {varname}")
        cdo.timmean(input=f"-selmon,9,10,11 -selname,{varname} {merged_file}", output=varfile)
    
    else:
        logger.error(f"Interval {interval} is not recognized. Please use 'year', 'winter', 'spring', 'summer', or 'fall'.")
        raise ValueError(f"Interval {interval} is not recognized. Please use 'year', 'winter', 'spring', 'summer', or 'fall'.")

    return None


@error_handling_decorator
def detrend(expname, varname, leg):
    """Detrend data by subtracting the time average using the CDO Python package."""
    
    dirs = folders(expname)
    varfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}.nc")
    anomfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    remove_existing_file(anomfile)

    logger.info(f"Detrending variable {varname} by subtracting the time average.")
    
    # Detrending using CDO: subtract the time mean from the variable
    cdo.sub(input=[varfile, f"-timmean {varfile}"], output=anomfile)

    return None


@error_handling_decorator
def get_EOF(expname, varname, leg, window):
    """Compute EOF using the CDO Python package with error handling."""

    # Get the directories and file paths
    dirs = folders(expname)

    # Define file paths for anomaly, covariance, and pattern output files
    flda = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_anomaly.nc")
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_variance.nc")
    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_pattern.nc")
    
    # Remove existing output files if they already exist
    remove_existing_file(fldcov)
    remove_existing_file(fldpat)

    logger.info(f"Computing EOF for variable {varname} with window size {window}.")
    
    # CDO command to compute EOFs
    cdo.eof3d(window, input=flda, output=fldcov)
    
    # Compute EOF patterns
    cdo.eof3d(window, input=flda, output=fldpat)

    # Define timeseries output file pattern
    timeseries = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_series_")
    
    # Remove existing timeseries files
    remove_existing_filelist(timeseries)

    # Compute EOF coefficients (timeseries)
    logger.info(f"Computing EOF coefficients for {varname}.")
    cdo.eofcoeff3d(input=[fldpat, flda], output=timeseries)

    logger.info(f"EOF computation completed successfully: {fldcov}, {fldpat}, {timeseries}")
    
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

    logger.info(f"Adding trend to {varname} using {auxfile} and {inifile}.")

    # CDO command to add the trend back to the detrended data
    cdo.add(input=[auxfile, f"-timmean {inifile}"], output=newfile)

    logger.info(f"Retrended forecast data created: {newfile}")

    return None


@error_handling_decorator
def EOF_info(expname, varname, leg):
    """Get the relative magnitude of EOF eigenvectors using the CDO Python package with error handling."""

    # Get the directories and file path for the covariance (variance) file
    dirs = folders(expname)
    cov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{varname}_variance.nc")

    logger.info(f"Getting relative magnitude of EOF eigenvectors for {varname} using {cov}")

    # CDO command to get relative magnitude (eigenvalues info) of the EOF eigenvectors
    cdo.info(input=f"-div {cov} -timsum {cov}")

    logger.info(f"Relative magnitude of EOF eigenvectors for {varname} computed successfully")

    return None


def merge_winter(expname, varname, startyear, endyear):
    """ CDO command to merge winter-only data """

    dirs = folders(expname)
    endleg = get_leg(endyear)
    os.makedirs(os.path.join(dirs['tmp'], str(endleg).zfill(3)), exist_ok=True)

    for year in range(startyear-1, endyear):
        filelist = []
        for i in range(2):
            pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year-i}-{year-i}.nc")
            matching_files = glob.glob(pattern)
            filelist.extend(matching_files)
        datafile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_data.nc")
        remove_existing_file(datafile)
        run_bash_command(f"cdo cat {' '.join(filelist)} {datafile}")
        varfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_monthly.nc")
        remove_existing_file(varfile)
        run_bash_command(f"cdo selname,{varname} {datafile} {varfile}")
        djfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_DJ.nc")
        remove_existing_file(djfile)
        run_bash_command(f"cdo selmon,12,1 {varfile} {djfile}")
        auxfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_DJ2.nc")
        remove_existing_file(auxfile)
        run_bash_command(f"cdo delete,timestep=1,-1 {djfile} {auxfile}")
        winterfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_winter_{year}.nc")
        remove_existing_file(winterfile)
        run_bash_command(f"cdo timmean {auxfile} {winterfile}")

    filelist = []
    for year in range(startyear-1, endyear):
        pattern = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_winter_{year}.nc")                        
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    datafile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}.nc")
    remove_existing_file(datafile)
    run_bash_command(f"cdo cat {' '.join(filelist)} {datafile}")

    auxfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"aux_")
    remove_existing_filelist(auxfile)

    return None

def merge_winter_only(expname, startyear, endyear, varname, dirs):
    """
    Process NEMO output files to focus on winter months (December and January),
    calculate a moving average, and merge the results using xarray and CDO.

    Parameters:
    - expname: experiment name.
    - startyear: the starting year of the time window.
    - endyear: the ending year of the time window.
    - var: variable name to process.
    - dirs: dictionary containing directory paths ('nemo' for input, 'tmp' for temporary files).
    """

    # Step 1: Load the data with xarray
    files = []
    for year in range(startyear, endyear + 1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}.nc")
        files.extend(glob.glob(pattern))

    # Combine all files into a single dataset
    ds = xr.open_mfdataset(files, combine='by_coords')

    # Step 2: Select the variable and group by month to filter December and January
    ds_var = ds[varname]

    # Group by month and filter out only December (12) and January (1)
    ds_winter = ds_var.groupby('time.month').filter(lambda x: x.month in [12, 1])

    # Step 3: Remove the first January and the last December
    ds_winter = ds_winter.where(~((ds_winter['time.month'] == 1) & (ds_winter['time.year'] == startyear)), drop=True)
    ds_winter = ds_winter.where(~((ds_winter['time.month'] == 12) & (ds_winter['time.year'] == endyear)), drop=True)

    # Step 4: Calculate a moving average with a window of 2 months (for Dec-Jan pairs)
    ds_winter_avg = ds_winter.rolling(time=2, center=True).mean().dropna('time', how='all')

    # Step 5: Use CDO for further processing (if needed)
    temp_file = os.path.join(dirs['tmp'], f"{varname}_winter_{startyear}_{endyear}_temp.nc")
    final_file = os.path.join(dirs['tmp'], f"{varname}_winter_{startyear}_{endyear}.nc")
    ds_winter_avg.to_netcdf(temp_file)

    # Example of a CDO operation (e.g., to further clean up or process the data)
    # Here, we might calculate the final average over all winters or perform a time mean
    cdo.timmean(input=temp_file, output=final_file)

    # Remove the temporary file
    os.remove(temp_file)

    return final_file