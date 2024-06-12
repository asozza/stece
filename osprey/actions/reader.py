#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reader module

Author: Alessandro Sozza
Date: June 2024
"""

import os
import glob
import shutil
import logging
import numpy as np
import xarray as xr

from osprey.utils.folders import folders

##########################################################################################
# Readers of NEMO output

def _nemodict(grid, freq):
    """Dictionary of NEMO output fields"""

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
    """General preprocessing routine for NEMO data based on grid type"""
    
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
    """Main function to read nemo data"""

    dirs = folders(expname)
    dict = _nemodict(grid, freq)

    filelist = []
    for year in range(startyear, endyear+1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_{dict[grid]['format']}_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    logging.info(' Files to be loaded %s', filelist)
    data = xr.open_mfdataset(filelist, preprocess=lambda d: dict[grid]["preproc"](d, grid), use_cftime=True)

    return data


##########################################################################################
# Reader of NEMO domain

def preproc_nemo_domain(data):
    """ preprocessing routine for nemo domain """

    data = data.rename({'time_counter': 'time'})

    return data

def read_domain(expname):
    """ read NEMO domain configuration file """

    dirs = folders(expname)
    filename = os.path.join(dirs['exp'], 'domain_cfg.nc')
    domain = xr.open_mfdataset(filename, preprocess=preproc_nemo_domain)
    domain = domain.isel(time=0)

    return domain

def elements(expname):
    """ define differential forms for integrals """

    df = {}
    domain = read_domain(expname)
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
    data = xr.open_mfdataset(filelist, use_cftime=True)

    return data

##########################################################################################

