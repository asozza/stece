#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Means module

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import numpy as np
import xarray as xr
import cftime

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

def timemean(data, varname):
    """ Time average of a field """

    ave = data[varname].mean(dim=['time'])

    return ave


def globalmean(data, varname, ndim, ztag=None, orca='ORCA2'):
    """ Global average of a field """

    #expname = get_expname(data)
    df = elements(orca)
    if ndim == '3D':
        ave = data[varname].weighted(df['V']).mean(dim=['time', 'z', 'y', 'x'])
        if ztag != None:
            z1,z2 = zlayer(ztag, orca)
            subvol = df['V'].isel(z=slice(z1,z2))
            subvar = data[varname].isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x'])
    elif ndim == '2D':
        ave = data[varname].weighted(df['S']).mean(dim=['time', 'y', 'x'])
    elif ndim == '1D':
        ave = data[varname].weighted(df['z']).mean(dim=['time', 'z'])
    else:
        raise ValueError(" Invalid dimensions ")

    return ave


def spacemean(data, varname, ndim, ztag=None, orca='ORCA2'):
    """ Spatial average of a field """

    #expname = get_expname(data)
    df = elements(orca) 
    if ndim == '3D':
        ave = data[varname].weighted(df['V']).mean(dim=['z', 'y', 'x'])
        if ztag != None:
            z1,z2 = zlayer(ztag, orca)
            subvol = df['V'].isel(z=slice(z1,z2))
            subvar = data[varname].isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['z', 'y', 'x'])
    elif ndim == '2D':
        ave = data[varname].weighted(df['S']).mean(dim=['y', 'x'])
    elif ndim == '1D':
        ave = data[varname].weighted(df['z']).mean(dim=['z'])
    else:
        raise ValueError(" Invalid dimensions ")

    return ave


#################################################################################
# OCEAN LAYERS

def zlayer(ztag, orca):
    """     
    Definition of vertical ocean layers for ORCAs 
    MIX: mixed layer (0-100 m), PYC: pycnocline (100-1000 m), ABY: abyss (1000-5000 m)
    levels in ORCA2: [0,9] [10,20] [21,30]
    levels in eORCA1: [0,23] [24,45] [46,74]

    Args:
        ztag (string): mix, pyc, aby
        orca (string): ORCA2,eORCA1
            
    """

    if orca == 'ORCA2':
        if ztag == 'mix':
            z1 = 0; z2 = 9
        elif ztag == 'pyc':
            z1 = 10; z2 = 20
        elif ztag == 'aby':
            z1 = 21; z2 = 30
        else:
            raise ValueError(" Invalid subrange ")
    elif orca == 'eORCA1':
        if ztag == 'mix':
            z1 = 0; z2 = 23
        elif ztag == 'pyc':
            z1 = 24; z2 = 45
        elif ztag == 'aby':
            z1 = 46; z2 = 74
        else:
            raise ValueError(" Invalid subrange ")
    else:
        raise ValueError(" Invalid ORCA grid ")
    
    return z1,z2

#################################################################################
# TOOLS FOR THE FORECAST (COST FUNCTIONS AND FORECAST ERROR)

def cost(x, x0, metric):
    """
    Calculate various cost functions based on the given metric.

    Args:
        x: The current value or array-like.
        x0: The reference value or array-like.
        metric: The metric used to compute the cost. Options include:
            - 'base': Original value
            - 'norm': Normalized value [x / x0]
            - 'diff': Difference [x - x0]
            - 'reldiff': Relative difference [(x - x0) / x0)]
            - 'abserr': Absolute error [|x - x0|]
            - 'relerr': Relative error [|x - x0| / x0]
            - 'sqerr': Squared error [(x - x0)^2]
            - 'relsqerr': Relative squared error [(x - x0)^2 / x0^2]

    Returns:
        The result of the chosen cost function (float or array-like)
    """
    
    if metric == 'base':
        return x    
    elif metric == 'norm':
        return np.divide(x, x0, out=np.zeros_like(x), where=x0 != 0)  # Prevent division by zero
    elif metric == 'diff':
        return x - x0
    elif metric == 'rdiff':
        return np.divide(x - x0, x0, out=np.zeros_like(x), where=x0 != 0)  # Prevent division by zero
    elif metric == 'abs':
        return np.abs(x - x0)
    elif metric == 'rel':
        return np.divide(np.abs(x - x0), x0, out=np.zeros_like(x), where=x0 != 0)  # Prevent division by zero
    elif metric == 'var':
        return np.power(x - x0, 2)
    elif metric == 'rvar': 
        return np.divide(np.power(x - x0, 2), np.power(x0, 2), out=np.zeros_like(x), where=x0 != 0)  # Prevent division by zero
    else:
        raise ValueError(f"Unknown metric: {metric}")


