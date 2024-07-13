#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Means module

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import numpy as np
from osprey.utils.utils import get_expname
from osprey.actions.reader import elements


#################################################################################
# TYPES OF AVERAGING

def movave(ydata, N):
    """ Moving average """

    #y_list = np.array(ydata.values.flatten())
    y_padded = np.pad(ydata, (N//2, N-1-N//2), mode='edge')
    y_smooth = np.convolve(y_padded, np.ones((N,))/N, mode='valid')

    return y_smooth


def cumave(ydata):
    """ Cumulative average """

    ave = np.cumsum(ydata)
    for i in range(1,len(ydata)):
        ave[i] = ave[i]/(i+1)

    return ave

#################################################################################
# FIELD AVERAGING
#
# Definitions: 
# global_mean:  time and space average
# time_mean:    time average
# space_mean:   space average
#

def timemean(data, var):
    """ Time average of a field """

    ave = data[var].mean(dim=['time'])

    return ave


def globalmean(data, var, ndim, subreg = None):
    """ Global average of a field """

    expname = get_expname(data)
    df = elements(expname)
    if ndim == '3D':
        ave = data[var].weighted(df['V']).mean(dim=['time', 'z', 'y', 'x'])
        if subreg != None:
            z1,z2 = subregions(subreg,'ORCA2')
            subvol = df['V'].isel(z=slice(z1,z2))
            subvar = data[var].isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x'])
    elif ndim == '2D':
        ave = data[var].weighted(df['S']).mean(dim=['time', 'y', 'x'])
    elif ndim == '1D':
        ave = data[var].weighted(df['z']).mean(dim=['time', 'z'])
    else:
        raise ValueError(" Invalid dimensions ")

    return ave


def spacemean(data, var, ndim, subregion=None, orca = 'ORCA2'):
    """ Spatial average of a field """

    expname = get_expname(data)
    df = elements(expname) 
    if ndim == '3D':
        ave = data[var].weighted(df['V']).mean(dim=['z', 'y', 'x'])
        if subregion != None:
            z1,z2 = subregions(subregion, orca)
            subvol = df['V'].isel(z=slice(z1,z2))
            subvar = data[var].isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['z', 'y', 'x'])
    elif ndim == '2D':
        ave = data[var].weighted(df['S']).mean(dim=['y', 'x'])
    elif ndim == '1D':
        ave = data[var].weighted(df['z']).mean(dim=['z'])
    else:
        raise ValueError(" Invalid dimensions ")

    return ave


#################################################################################
# SUBREGIONS

def subregions(idx, orca):
    """     
    Definition of vertical subregions for ORCAs 
    mixed layer (0-100 m), pycnocline (100-1000 m), abyss (1000-5000 m)
    levels in ORCA2: [0,9] [10,20] [21,30]
    levels in eORCA1: [0,23] [24,45] [46,74]

    Args:
        idx (string): mix, pyc, aby
        orca (string): ORCA2,eORCA1
            
    """

    if orca == 'ORCA2':
        if idx == 'mixed-layer':
            z1 = 0; z2 = 9
        elif idx == 'pycnocline':
            z1 = 10; z2 = 20
        elif idx == 'abyss':
            z1 = 21; z2 = 30
        else:
            raise ValueError(" Invalid subrange ")
    elif orca == 'eORCA1':
        if idx == 'mixed-layer':
            z1 = 0; z2 = 23
        elif idx == 'pycnocline':
            z1 = 24; z2 = 45
        elif idx == 'abyss':
            z1 = 46; z2 = 74
        else:
            raise ValueError(" Invalid subrange ")
    else:
        raise ValueError(" Invalid ORCA grid ")
    
    return z1,z2

#################################################################################
# TOOLS FOR THE FORECAST (COST FUNCTIONS AND FORECAST ERROR)

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
        x = np.abs(var-varref)
    # relative error
    if idx == 'rel':
        x = np.abs(var-varref)/varref
    # variance
    if idx == 'var':
        x = np.power(var-varref,2)
    # normalized/relative variance
    if idx == 'rvar':
        x = np.power(var-varref,2)/np.power(varref,2)
    # other cost functions: exp? or atan?

    return x


# # mean state
# def mean_state(expname, startyear, endyear):

#     df = elements(expname=expname)
#     data = read_T(expname=expname, startyear=startyear, endyear=endyear)
#     field = data.mean(dim=['time'])
#     field = field.drop_dims({'axis_nbounds'})

#     return field


# def anomaly_local(expname, year, field, idx):
    
#     data = read_T(expname=expname, year=year)
#     delta = cost(data, field, idx)

#     return delta


def mean_forecast_error(expname, year, var, xfield):
     """ function to compute mean forecast error """

     df = elements(expname=expname)
     data = read_T(expname=expname, year=year)
     mdata = data[var].mean('time')
     xdata = xr.where(mdata!=0.0, xfield, 0.0)
     delta = xr.where(mdata!=0.0, mdata.values-xdata.values, 0.0)
     dd = delta.weighted(df['vol']).mean(dim=['z', 'y', 'x']).values

     return dd
