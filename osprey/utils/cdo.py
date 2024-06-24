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

from osprey.utils.folders import folders
from osprey.utils.utils import run_bash_command, remove_existing_file, remove_existing_filelist
from osprey.utils.time import get_leg


def merge(expname, startyear, endyear):
    """ CDO command to merge files """

    dirs = folders(expname)
    leg = get_leg(endyear)

    filelist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)
    merged_file = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")
    remove_existing_file(merged_file)
    run_bash_command(f"cdo cat {' '.join(filelist)} {merged_file}")

    return None

def selname(expname, startyear, endyear, var):
    """ CDO command to select variable """

    dirs = folders(expname)
    leg = get_leg(endyear)

    merged_file = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")
    varfile = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}.nc")
    remove_existing_file(varfile)

    run_bash_command(f"cdo yearmean -selname,{var} {merged_file} {varfile}")

    return None

def detrend(expname, startyear, endyear, var):
    """ CDO command to detrend, subtracting time average """

    dirs = folders(expname)
    leg = get_leg(endyear)

    varfile = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}.nc")   
    anomfile = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly.nc")
    remove_existing_file(anomfile)

    run_bash_command(f"cdo sub {varfile} -timmean {varfile} {anomfile}")

    return None

def get_EOF(expname, startyear, endyear, var):
    """ CDO command to compute EOF """
    

    dirs = folders(expname)
    leg = get_leg(endyear)
    window = endyear - startyear
    #print(' Time window = ',window)
    print(' Time window ', window)

    flda = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly.nc") 
    #flda = os.path.join(f"{var}_anomaly_{startyear}-{endyear}.nc")    
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance.nc")
    #fldcov = os.path.join(f"{var}_var_{startyear}-{endyear}.nc")
    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_pattern.nc")
    #fldpat = os.path.join(f"{var}_pat_{startyear}-{endyear}.nc")
    remove_existing_file(fldcov)
    remove_existing_file(fldpat)

    #if ndim == '2D':
    # run_bash_command(f"cdo eof,{window} {flda} {fldcov} {fldpat}")
    #if ndim == '3D':
    run_bash_command(f"cdo eof3d,{window} {flda} {fldcov} {fldpat}")

    timeseries = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_series_")
    #timeseries = os.path.join(f"{var}_tseries_{startyear}-{endyear}_")
    remove_existing_filelist(timeseries)
    run_bash_command(f"cdo eofcoeff3d {fldpat} {flda} {timeseries}")

    return None

def retrend(expname, startyear, endyear, var):
    """ CDO command to add trend """

    dirs = folders(expname)
    endleg = get_leg(endyear)

    # add mean time trend to the anomaly 
    inifile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}.nc")
    auxfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_product.nc")
    newfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast.nc")
    remove_existing_file(newfile)

    run_bash_command(f"cdo add {auxfile} -timmean {inifile} {newfile}")

    return None

def EOF_info(expname, startyear, endyear, var):
    """ get relative magnitude of EOF eigenvectors """

    dirs = folders(expname)
    leg = get_leg(endyear)

    cov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance.nc")

    run_bash_command(f"cdo info -div {cov} -timsum {cov}")

    return None

def merge_rebuilt(expname, startleg, endleg):
    """ CDO command to merge rebuilt restart files """

    dirs = folders(expname)

    filelist = []
    for leg in range(startleg, endleg+1):
        pattern = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc')
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    
    merged_file = os.path.join(dirs['tmp'], str(endleg).zfill(3), "rdata.nc")
    remove_existing_file(merged_file)
    run_bash_command(f"cdo cat {' '.join(filelist)} {merged_file}")

    return None