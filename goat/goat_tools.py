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
import glob
import numpy as np
import xarray as xr
import cftime
import datetime
import time
from sklearn.linear_model import LinearRegression

def epoch(date):

    s = time.mktime(date.timetuple())

    return s

def yearFraction(date):

    StartOfYear = datetime.datetime(date.year,1,1,0,0,0)
    EndOfYear = datetime.datetime(date.year+1,1,1,0,0,0)
    yearElapsed = epoch(date)-epoch(StartOfYear)
    yearDuration = epoch(EndOfYear)-epoch(StartOfYear)
    Frac = yearElapsed/yearDuration

    return  date.year + Frac

def dateDecimal(date):

    x1 = [yearFraction(t) for t in date]

    return x1

# container for multiple cost functions
def cost(var, varref, idx):

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
def subregions(orca):

    z1 = []; z2 = []
    if orca == 'ORCA2':
        z1 = [0, 10, 21]
        z2 = [9, 20, 30]
    elif orca == 'eORCA1':
        z1 = [0, 24, 46]
        z2 = [23, 45, 74]
    else:        
        raise ValueError(" Not a valid ORCA grid! ")
    
    return z1,z2