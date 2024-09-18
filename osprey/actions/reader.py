#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reader module

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC)
Date: June 2024
"""

import os
import glob
import yaml
import logging
import xarray as xr
import dask

from osprey.utils.folders import folders, paths
from osprey.utils.run_cdo import merge

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# dask optimization
dask.config.set({'array.optimize_blockwise': True})

##########################################################################################
# Readers of NEMO output

def _nemodict(grid, freq):
    """ 
    Nemodict: Dictionary of NEMO output fields
    
    Args: 
    grid: grid name [T, U, V, W]
    freq: output frequency [1m, 1y, ...]

    """


    gridlist = ["T", "U", "V", "W"]    
    if grid in gridlist:
        grid_lower = grid.lower()
        return {
            grid: {
                "preproc": preproc_nemo,
                "format": f"oce_{freq}_{grid}",
                "x_grid": f"x_grid_{grid}",
                "y_grid": f"y_grid_{grid}",
                "nav_lat": f"nav_lat_grid_{grid}",
                "nav_lon": f"nav_lon_grid_{grid}",
                "depth": f"depth{grid_lower}",
                "x_grid_inner": f"x_grid_{grid}_inner",
                "y_grid_inner": f"y_grid_{grid}_inner"
            }
        }
    elif grid == "ice":
        return {
            "ice": {
                "preproc": preproc_nemo_ice,
                "format": f"ice_{freq}"
            }
        }
    else:
        raise ValueError(f"Unsupported grid type: {grid}")


def preproc_nemo(data, grid):
    """ 
    General preprocessing routine for NEMO data based on grid type
    
    Args: 
    data: dataset
    grid: gridname [T, U, V, W]

    """
    
    grid_mappings = _nemodict(grid, None)[grid]  # None for freq as it is not used here

    data = data.rename_dims({grid_mappings["x_grid"]: 'x', grid_mappings["y_grid"]: 'y'})
    data = data.rename({
        grid_mappings["nav_lat"]: 'lat', 
        grid_mappings["nav_lon"]: 'lon', 
        grid_mappings["depth"]: 'z', 
        'time_counter': 'time'
    })
    data = data.swap_dims({grid_mappings["x_grid_inner"]: 'x', grid_mappings["y_grid_inner"]: 'y'})
    data = data.drop_vars(['time_centered'], errors='ignore')
    data = data.drop_dims(['axis_nbounds'], errors='ignore')

    return data


def preproc_nemo_ice(data):
    """Preprocessing routine for NEMO for ice"""

    data = data.rename({'time_counter': 'time'})
    
    return data


def reader_nemo(expname, startyear, endyear, grid="T", freq="1m"):
    """ 
    Reader_nemo: Main function to read NEMO data 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    grid: grid name [T, U, V, W]
    frequency: output frequency [1m, 1y, ...]

    """

    dirs = folders(expname)
    dict = _nemodict(grid, freq)

    filelist = []
    available_years = []
    for year in range(startyear, endyear + 1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_{dict[grid]['format']}_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        if matching_files:
            filelist.extend(matching_files)
            available_years.append(year)

    if not filelist:
        raise FileNotFoundError(f"No data files found for the specified range {startyear}-{endyear}.")

    # Log a warning if some years are missing
    if available_years:
        actual_startyear = min(available_years)
        actual_endyear = max(available_years)
        if actual_startyear > startyear or actual_endyear < endyear:
            logging.warning(f"Data available only in the range {actual_startyear}-{actual_endyear}.")
    else:
        raise FileNotFoundError("No data files found within the specified range.")

    logging.info('Files to be loaded %s', filelist)
    data = xr.open_mfdataset(filelist, preprocess=lambda d: dict[grid]["preproc"](d, grid), use_cftime=True)

    return data


def reader_meanfield():
    """ Read/compute mean field using cdo """

    # read info about meanfield from yaml file
    local_paths = paths()
    filename = os.path.join(local_paths['osprey'], 'meanfield.yaml')
    with open(filename) as yamlfile:
        info = yaml.load(yamlfile, Loader=yaml.FullLoader)
    keys = ['expname', 'startyear', 'endyear', 'orca', 'grid', 'freq', 'replace']
    expname, startyear, endyear, orca, grid, freq, replace = [info[key] for key in keys]

    logger.info(f"Loading mean field for expname={expname}, startyear={startyear}, endyear={endyear}")

    dirs = folders(expname)
    dict = _nemodict(grid, freq)
    filename = os.path.join(dirs['nemo'], f"{expname}_{grid}_{startyear}-{endyear}.nc")

    if not filename:
        raise FileNotFoundError(f"No data file found.")
        # create file
        merge(expname, startyear, endyear)

    logging.info('Files to be loaded %s', filename)
    data = xr.open_mfdataset(filename, preprocess=lambda d: dict[grid]["preproc"](d, grid), use_cftime=True)
    
    return data



##########################################################################################
# Reader of NEMO domain

def preproc_nemo_domain(data):
    """ Pre-processing routine for nemo domain """

    data = data.rename({'time_counter': 'time'})

    return data

def read_domain(orca):
    """ Read NEMO domain configuration file """

    dirs = paths()
    filename = os.path.join(dirs['domain'], orca, 'domain_cfg.nc')
    domain = xr.open_mfdataset(filename, preprocess=preproc_nemo_domain)
    domain = domain.isel(time=0)

    return domain

def elements(orca):
    """ Define differential forms for integrals """

    df = {}
    domain = read_domain(orca)
    df['V'] = domain['e1t']*domain['e2t']*domain['e3t_0']
    df['S'] = domain['e1t']*domain['e2t']
    df['x'] = domain['e1t']
    df['y'] = domain['e2t']
    df['z'] = domain['e3t_0']

    return df

##########################################################################################
# Reader of NEMO restart (rebuilt)

def reader_rebuilt(expname, startleg, endleg):
    """ Read rebuilt NEMO restart files """

    dirs = folders(expname)
    
    filelist = []
    for leg in range(startleg,endleg+1):
        pattern = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc')
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    logging.info(' File to be loaded %s', filelist)
    data = xr.open_mfdataset(filelist, use_cftime=True)

    return data

##########################################################################################

