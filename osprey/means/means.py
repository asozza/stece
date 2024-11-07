#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mathematical Means module

Author: Alessandro Sozza (CNR-ISAC)
Date: Mar 2024
"""

import numpy as np
import xarray as xr
import cftime
import dask
from scipy.interpolate import interp1d

from osprey.actions.reader import elements

#dask.config.set({'array.optimize_blockwise': True})

def flatten_to_triad(m, nj, ni):
    """ Recover triad indexes from flatten array length """

    k = m // (ni * nj)
    j = (m - k * ni * nj) // ni
    i = m - k * ni * nj - j * ni

    return k, j, i

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

def timemean_old(data):
    """ 
    Time average of a field 
    
    Args:
    data (DataArray): field

    """

    ave = data.mean(dim=['time'])

    return ave

def timemean(data, format='global'):
    """ 
    Time average of a field with various options
    
    Args:
    data (DataArray): Input field with a time dimension.
    format (str): Type of time averaging. Options are:
                  - 'global': average over all time points.
                  - 'monthly': average by month across years.
                  - 'seasonally': average by season (DJF, MAM, JJA, SON) across years.
                  - 'yearly': average by year.
                                    
    Returns:
    DataArray: Time-averaged field based on the specified format.
    """
    
    if format == 'plain':
        ave = data

    elif format == 'global':
        # Global time average over all time points
        ave = data.mean(dim='time')
        
    elif format == 'monthly':
        # Average by month across years
        ave = data.groupby('time.month').mean(dim='time')
        
    elif format == 'seasonally':
        # Average by season (DJF, MAM, JJA, SON) across years
        ave = data.groupby('time.season').mean(dim='time')
        
    elif format == 'yearly':
        # Average by year
        ave = data.groupby('time.year').mean(dim='time')

    else:
        raise ValueError("Invalid format specified. Choose from: 'plain', 'global', 'monthly', 'seasonally', 'yearly'.")
    
    return ave

def globalmean(data, ndim, ztag=None, orca='ORCA2'):
    """ 
    Global average of a field 
    
    Args:
    data (DataArray): field
    ndim (string): dimensions <'1D','2D','3D'>
    ztag (string): tag for sublayers <mix,pyc,aby>
    orca (string): ORCA resolution <ORCA2,eORCA...>
    
    """

    #expname = get_expname(data)
    df = elements(orca)
    if ndim == '3D':
        ave = data.weighted(df['V']).mean(dim=['time', 'z', 'y', 'x'])
        if ztag != None:
            z1,z2 = zlayer(ztag, orca)
            subvol = df['V'].isel(z=slice(z1,z2))
            subvar = data.isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x'])
    elif ndim == '2D':
        ave = data.weighted(df['S']).mean(dim=['time', 'y', 'x'])
    elif ndim == '1D':
        ave = data.weighted(df['z']).mean(dim=['time', 'z'])
    else:
        raise ValueError(" Invalid dimensions ")

    return ave


def spacemean(data, ndim, ztag=None, orca='ORCA2'):
    """ 
    Spatial average of a field 
    
    Args:
    data (DataArray): field
    ndim (string): dimensions <'1D','2D','3D'>
    ztag (string): tag for sublayers <mix,pyc,aby>
    orca (string): ORCA resolution <ORCA2,eORCA...>
    
    """

    #expname = get_expname(data)
    df = elements(orca) 
    if ndim == '3D':
        ave = data.weighted(df['V']).mean(dim=['z', 'y', 'x'])
        if ztag != None:
            z1,z2 = zlayer(ztag, orca)
            subvol = df['V'].isel(z=slice(z1,z2))
            subvar = data.isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['z', 'y', 'x'])
    elif ndim == '2D':
        ave = data.weighted(df['S']).mean(dim=['y', 'x'])
    elif ndim == '1D':
        ave = data.weighted(df['z']).mean(dim=['z'])
    else:
        raise ValueError(" Invalid dimensions ")

    return ave


#################################################################################
# OCEAN LAYERS

def zlayer(ztag, orca):
    """     
    Vertical ocean layers for ORCAs 
    
    MIX: mixed layer (0-100 m), PYC: pycnocline (100-1000 m), ABY: abyss (1000-5000 m)
    levels in ORCA2: [0,9] [10,20] [21,30]
    levels in eORCA1: [0,23] [24,45] [46,74]

    Args:
        ztag (string): <mix, pyc, aby>
        orca (string): <ORCA2,eORCA1>
            
    """

    if orca == 'ORCA2':
        if ztag == 'mix':
            z1 = 0; z2 = 9
        elif ztag == 'pyc':
            z1 = 10; z2 = 20
        elif ztag == 'aby':
            z1 = 21; z2 = 30
        else:
            raise ValueError(" Invalid z-tag ")
    elif orca == 'eORCA1':
        if ztag == 'mix':
            z1 = 0; z2 = 23
        elif ztag == 'pyc':
            z1 = 24; z2 = 45
        elif ztag == 'aby':
            z1 = 46; z2 = 74
        else:
            raise ValueError(" Invalid z-tag ")
    else:
        raise ValueError(" Invalid ORCA grid ")
    
    return z1,z2


#################################################################################
# TOOLS FOR THE FORECAST
#
# - cost function
# - forecast error?
# - year shifting / year gain
#

def cost(x, x0, metric):
    """
    Calculate various cost functions based on the given metric.

    Args:
        x (xarray.DataArray): The current value.
        x0 (xarray.DataArray): The reference value.
        metric (str): The metric used to compute the cost.
        Options include:
            - 'base': Original value
            - 'norm': Normalized value [x / x0]
            - 'diff': Difference [x - x0]
            - 'reldiff': Relative difference [(x - x0) / x0)]
            - 'abserr': Absolute error [|x - x0|]
            - 'relerr': Relative error [|x - x0| / x0]
            - 'sqerr': Squared error [(x - x0)^2]
            - 'relsqerr': Relative squared error [(x - x0)^2 / x0^2]

    Returns:
        xarray.DataArray: The result of the chosen cost function.
    """
    if metric == 'base':
        return x    

    elif metric == 'norm':
        return xr.where(x0 != 0.0, x / x0, 0.0)  # Prevent division by zero

    elif metric == 'diff':
        return x - x0

    elif metric == 'reldiff':
        return xr.where(x0 != 0.0, x / x0 - 1.0, 0.0)

    elif metric == 'abs':
        return np.abs(x - x0)

    elif metric == 'relabs':        
        return xr.where(x0 != 0.0, np.abs(x / x0 - 1.0), 0.0)

    elif metric == 'sqerr':
        return np.pow(x - x0, 2)

    elif metric == 'relsqerr':
        return xr.where(x0 != 0.0, np.pow(x/x0, 2) - 2.0*(x/x0) + 1.0, 0.0)

    else:
        raise ValueError(f"Unknown metric: {metric}")


def apply_cost_function(data, mdata, metric, format='global'):
    """
    Apply a cost function to data based on `format`.

    Args:
        data (xarray.DataArray): The current dataset.
        mdata (xarray.DataArray): The reference dataset.
        metric (str): The metric used to compute the cost.
        format (str, optional): Time format ['plain', 'monthly', 'seasonally', 'yearly', 'global']

    Returns:
        xarray.DataArray: Data containing the computed cost metrics.
    """

    if (format == 'global' or format == 'plain'): 
        cdata = cost(data, mdata, metric)

    if format == 'monthly':
        if 'time' in data.dims and 'month' in mdata.dims:
            cdata = data.groupby("time.month").map(lambda x: cost(x, mdata.sel(month=x['time.month']), metric))

    if format == 'seasonally':
        if 'time' in data.dims and 'season' in mdata.dims:
            cdata = data.groupby("time.season").map(lambda x: cost(x, mdata.sel(season=x['time.season']), metric))

    if format == 'yearly':
        if 'time' in data.dims and 'year' in mdata.dims:
            cdata = data.groupby("time.year").map(lambda x: cost(x, mdata.sel(season=x['time.year']), metric))

    return cdata


def year_shift(x1, y1, x2, y2, shift_threshold=20.0):
    """ 
    Compute year shift/gain between two timeseries (relative to curve 1) 
    
    Args:
    (x1,y1): coordinates of curve 1
    (x2,y2): coordinates of curve 2 (usually REF exp.)
    shift_threshold: maximum acceptable value of year shift

    """

    # Interpolate curve 2 with respect to y-values to get x2 = f(y2)
    interp_curve2_inv = interp1d(y2, x2, kind='linear', bounds_error=False, fill_value="extrapolate")
    
    # List to store the horizontal shift for each point of curve 1
    shifts = []
    
    # Calculate the shift for each point in curve 1
    for i in range(len(x1)):
        y1_point = y1[i]  # y-value of curve 1
        x1_point = x1[i]  # x-value of curve 1

        # Find the corresponding x-value on curve 2 for the same y-value
        x2_point = interp_curve2_inv(y1_point)
        
        # Calculate the horizontal shift
        shift = x2_point - x1_point
        
        # Add a condition for the maximum acceptable shift threshold
        if abs(shift) > shift_threshold:
            shift = np.nan  # Ignore shifts that are too large (set to NaN)
        
        shifts.append(shift)
    
    return np.array(shifts)