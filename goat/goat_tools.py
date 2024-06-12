#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GOAT: Global Ocean & Atmosphere Trends
------------------------------------------------------
GOAT library for tools (options, simple functions & miscellanea)

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""


import os
import numpy as np
import xarray as xr
import cftime
import dask
import datetime
import time

def epoch(date):
    """ get epoch from date """

    s = time.mktime(date.timetuple())

    return s

def yearFraction(date):
    """ transform date into year fraction """

    StartOfYear = datetime.datetime(date.year,1,1,0,0,0)
    EndOfYear = datetime.datetime(date.year+1,1,1,0,0,0)
    yearElapsed = epoch(date)-epoch(StartOfYear)
    yearDuration = epoch(EndOfYear)-epoch(StartOfYear)
    Frac = yearElapsed/yearDuration

    return  date.year + Frac

def dateDecimal(date):
    """ apply yearFraction to an array of dates """

    x1 = [yearFraction(t) for t in date]

    return x1

def get_expname(data):
    """" Get expname from a NEMO dataset & output file path """

    return os.path.basename(data.attrs['name']).split('_')[0]

def get_nemo_timestep(filename):
    """ Get timestep from a NEMO restart file """

    return os.path.basename(filename).split('_')[1]

# container for multiple cost functions
def cost(var, varref, idx):
    """ multiple cost functions """

    # normalized
    if idx == 'norm':
        x = var/varref
    # difference (with sign)
    if idx == 'diff':
        x = (var-varref)
    # relative difference
    if idx == 'rdiff':
        x = (var-varref)/varref    
    # absolute error
    if idx == 'abs':
        x = abs(var-varref)
    # relative error
    if idx == 'rel':
        x = abs(var-varref)/varref
    # variance
    if idx == 'var':
        x = pow(var-varref,2)
    # normalized/relative variance
    if idx == 'rvar':
        x = pow(var-varref,2)/pow(varref,2)
    # other cost functions: exp? or atan?

    return x

# VERTICAL SUBREGIONS
# mixed layer (0-100 m), pycnocline (100-1000 m), abyss (1000-5000 m)
# levels in ORCA2: [0,9] [10,20] [21,30]
# levels in eORCA1: [0,23] [24,45] [46,74]
def subrange(idx, orca):
    """ definition of vertical subregions (mixed layer, pycnocline & abyss) for ORCAs """

    if orca == 'ORCA2':
        if idx == 'mix':
            z1 = 0; z2 = 9
        elif idx == 'pyc':
            z1 = 10; z2 = 20
        elif idx == 'aby':
            z1 = 21; z2 = 30
        else:
            raise ValueError(" Invalid subrange ")
    elif orca == 'eORCA1':
        if idx == 'mix':
            z1 = 0; z2 = 23
        elif idx == 'pyc':
            z1 = 24; z2 = 45
        elif idx == 'aby':
            z1 = 46; z2 = 74
        else:
            raise ValueError(" Invalid subrange ")
    else:
        raise ValueError(" Invalid ORCA grid ")
    
    return z1,z2
