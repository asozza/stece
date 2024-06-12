#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CDO module

Author: Alessandro Sozza (CNR-ISAC) 
Date: June 2024
"""

import os
import glob
from osprey.utils.folders import folders
from osprey.utils.utils import run_bash_command
from osprey.utils.time import get_leg


def merge(expname, startyear, endyear):
    """ CDO command to merge files """

    dirs = folders(expname)
    leg = get_leg(endyear)

    fldlist = []
    for year in range(startyear, endyear):
        pattern = os.path.join(dirs['nemo'], f"{expname}_oce_*_T_{year}-{year}.nc")
        matching_files = glob.glob(pattern)
        fldlist.extend(matching_files)
    
    os.makedirs(os.path.join(dirs['tmp'], str(leg).zfill(3)), exist_ok=True)
    fldcat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{expname}_{startyear}-{endyear}.nc")
    run_bash_command(f"cdo cat {' '.join(fldlist)} {fldcat}")

    return None

def selname(expname, startyear, endyear, var):
    """ CDO command to select variable """

    dirs = folders(expname)
    leg = get_leg(endyear)    

    fld = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    fldcat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{expname}_{startyear}-{endyear}.nc")

    run_bash_command(f"cdo yearmean -selname,{var} {fldcat} {fld}")

    return None

def detrend(expname, startyear, endyear, var):
    """ CDO command to detrend, subtracting time average """

    dirs = folders(expname)
    leg = get_leg(endyear)

    fld = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_{startyear}-{endyear}.nc")   
    flda = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly_{startyear}-{endyear}.nc")

    run_bash_command(f"cdo sub {fld} -timmean {fld} {flda}")

    return None

def get_EOF(expname, startyear, endyear, var, ndim):
    """ CDO command to compute EOF """
    
    dirs = folders(expname)
    leg = get_leg(endyear)
    window = endyear - startyear

    flda = os.path.join(dirs['tmp'],  str(leg).zfill(3), f"{var}_anomaly_{startyear}-{endyear}.nc")    
    fldcov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance_{startyear}-{endyear}.nc")
    fldpat = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_pattern_{startyear}-{endyear}.nc")

    try:
        os.remove(fldcov)
        print(f"File {fldcov} successfully removed.")
    except FileNotFoundError:
        print(f"File {fldcov} not found. Unable to remove.")

    try:
        os.remove(fldpat)
        print(f"File {fldpat} successfully removed.")
    except FileNotFoundError:
        print(f"File {fldpat} not found. Unable to remove.")

    if ndim == '2D':
        run_bash_command(f"cdo eof,{window} {flda} {fldcov} {fldpat}")
    
    if ndim == '3D':
        run_bash_command(f"cdo eof3d,{window} {flda} {fldcov} {fldpat}")

    timeseries = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_timeseries_{startyear}-{endyear}_")
    run_bash_command(f"cdo eofcoeff {fldpat} {flda} {timeseries}")

    return None

def retrend(expname, startyear, endyear, var):
    """ CDO command to add trend """

    dirs = folders(expname)
    endleg = get_leg(endyear)

    # add mean time trend to the anomaly 
    inifile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_{startyear}-{endyear}.nc")
    auxfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_product_{startyear}-{endyear}.nc")
    newfile = os.path.join(dirs['tmp'], str(endleg).zfill(3), f"{var}_forecast_{startyear}-{endyear}.nc")

    try:
        os.remove(newfile)
        print(f"File {newfile} successfully removed.")
    except FileNotFoundError:
        print(f"File {newfile} not found. Unable to remove.")

    run_bash_command(f"cdo add {auxfile} -timmean {inifile} {newfile}")

    return None

def EOF_info(expname, startyear, endyear, var):
    """ get relative magnitude of EOF eigenvectors """

    dirs = folders(expname)
    leg = get_leg(endyear)

    cov = os.path.join(dirs['tmp'], str(leg).zfill(3), f"{var}_variance_{startyear}-{endyear}.nc")

    run_bash_command(f"cdo info -div {cov} -timsum {cov}")

    return None