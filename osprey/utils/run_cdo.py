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
from osprey.utils.time import get_leg, get_year


def merge(expname, startyear, endyear):
    """ CDO command to merge files """

    dirs = folders(expname)
    leg = get_leg(endyear)

    filelist = []
    for year in range(startyear-2, endyear+1):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        print(pattern)
        matching_files = glob.glob(pattern)
        filelist.extend(matching_files)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)
    merged_file = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")
    remove_existing_file(merged_file)
    
    run_bash_command(f"cdo cat {' '.join(filelist)} {merged_file}")

    return None

def selname(expname, var, leg, interval):
    """ CDO command to select variable """

    dirs = folders(expname)
    merged_file = os.path.join(dirs['tmp'], str(leg).zfill(3), "data.nc")
    varfile = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}.nc")
    remove_existing_file(varfile)

    if interval == 'year':
        run_bash_command(f"cdo yearmean -selname,{var} {merged_file} {varfile}")
    elif interval == 'winter':
        run_bash_command(f"cdo timmean -selmon,12,1,2 -selname,{var} {merged_file} {varfile}")
    else:
        print(f"Interval {interval} is not recognized. Please use 'year' or 'winter'.")

    return None

def detrend(expname, var, leg):
    """ CDO command to detrend, subtracting time average """

    dirs = folders(expname)
    varfile = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}.nc")   
    anomfile = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly.nc")
    remove_existing_file(anomfile)

    run_bash_command(f"cdo sub {varfile} -timmean {varfile} {anomfile}")

    return None

def get_EOF(expname, var, leg, window):
    """ CDO command to compute EOF """

    dirs = folders(expname)

    flda = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly.nc")   
    #window = run_bash_command(f"cdo ntime {flda} | head -n 1")
    print(' Time window ', window)

    # compute the basis (pattern + covariance matrix)
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance.nc")
    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_pattern.nc")
    remove_existing_file(fldcov)
    remove_existing_file(fldpat)
    run_bash_command(f"cdo eof3d,{window} {flda} {fldcov} {fldpat}")

    # compute timeseries (eigeinvalues?)
    timeseries = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_series_")
    remove_existing_filelist(timeseries)
    run_bash_command(f"cdo eofcoeff3d {fldpat} {flda} {timeseries}")

    return None

def retrend(expname, var, leg):
    """ CDO command to add trend """

    dirs = folders(expname)
    inifile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}.nc")
    auxfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_product.nc")
    newfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_forecast.nc")
    remove_existing_file(newfile)

    run_bash_command(f"cdo add {auxfile} -timmean {inifile} {newfile}")

    return None

def EOF_info(expname, var, leg):
    """ get relative magnitude of EOF eigenvectors """

    dirs = folders(expname)
    cov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance.nc")
    run_bash_command(f"cdo info -div {cov} -timsum {cov}")

    return None

def merge_rebuilt(expname, startleg, endleg):
    """ CDO command to merge rebuilt restart files """

    dirs = folders(expname)

    varlist=['tn', 'tb']

    for leg in range(startleg, endleg+1):
        filename = os.path.join(dirs['tmp'], str(leg).zfill(3), expname + '*_restart.nc')
        year = get_year(leg)
        for var in varlist:
            auxfile = os.path.join(dirs['tmp'], str(leg).zfill(3), "aux.nc")
            outfile = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_{leg}.nc")
            run_bash_command(f"cdo -selname,{var} {filename} {auxfile}")
            run_bash_command(f"cdo -settaxis,{year}-01-01,00:00:00,1year {auxfile} {outfile}")
            remove_existing_file(auxfile)
    
    varlist=['tn', 'tb']
    for var in varlist:
        filelist = []
        for leg in range(startleg, endleg+1):
            pattern = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_{leg}.nc")
            matching_files = glob.glob(pattern)
            filelist.extend(matching_files)
    
        merged_file = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_nt.nc")
        remove_existing_file(merged_file)
        run_bash_command(f"cdo cat {' '.join(filelist)} {merged_file}")

    return None

def merge_winter(expname, var, startyear, endyear):
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
        run_bash_command(f"cdo selname,{var} {datafile} {varfile}")
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

