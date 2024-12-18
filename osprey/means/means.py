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
import logging
from scipy.interpolate import interp1d

from osprey.actions.reader import elements

#dask.config.set({'array.optimize_blockwise': True})

# dictionary of months by seasons
season_months = {
        "DJF": [12, 1, 2], 
        "MAM": [3, 4, 5], 
        "JJA": [6, 7, 8], 
        "SON": [9, 10, 11],
        'winter': [12, 1, 2],
        'spring': [3, 4, 5],
        'summer': [6, 7, 8],
        'autumn': [9, 10, 11]
    }


#################################################################################
# matrix algebra

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

def timemean(data, format='global', use_cftime=True):
    """ 
    Time average of a field with various options
    
    Args:
    data (DataArray): Input field with a time dimension.
    format (str): Type of time averaging. Options are:
                  - 'global': average over all time points.
                  - 'monthly': average by month across years.
                  - 'seasonally': average by season (DJF, MAM, JJA, SON) across years.
                  - 'yearly': average by year.
                  - 'seasons': average by season yearly.
                  - 'winter,spring,summer,autumn': average by a single season yearly.

    Returns:
    DataArray: Time-averaged field based on the specified format.
    """
    
    if format == 'plain':
        ave = data

    elif format == 'global':
        # Global time average over all time points
        ave = data.mean(dim='time')
        
    # TO BE FIXED YET: monthly and seasonally sohuld be at center of the period.
    elif format == 'monthly':       
        # Average by month across years
        ave = data.groupby('time.month').mean(dim='time')
        
        if use_cftime:
            
            # create cftime array of dates
            last_year = data['time.year'].values[-1]
            dates = [cftime.DatetimeGregorian(last_year, month, 1, 0, 0, 0, has_year_zero=False) for month in range(1, 13)]
            
            # create new coordinates ( space unchanged)
            coords = {"time": dates}
            for dim in data.coords:
                if dim not in coords:
                    coords[dim] = data[dim]
            
            # combine all in a new array
            ave = xr.DataArray(
                data=ave, 
                dims=["time"] + [dim for dim in ave.dims if dim != "month"], # replace 'month' with 'time' 
                coords=coords
            )


    elif format == 'seasonally':
        # Average by season (DJF, MAM, JJA, SON) across years
        ave = data.groupby('time.season').mean(dim='time')

        if use_cftime:

            # create cftime array of dates
            last_year = data['time.year'].values[-1]
            dates = [cftime.DatetimeGregorian(last_year, month, 1, 0, 0, 0, has_year_zero=False) for month in range(1, 13)]

            # create new coordinates (space unchanged)
            coords = {"time": dates}
            for dim in data.coords:
                if dim not in coords:
                    coords[dim] = data[dim]

            # spread seasonal values across all months 
            values = []
            for month in range(1, 13):
                for season, months in season_months.items():
                    if month in months:
                        values.append(ave.sel(season=season).values)
                        break

            # put all in a new array
            ave = xr.DataArray(
                data=values, 
                dims=["time"] + [dim for dim in ave.dims if dim != "season"], # replace 'season' with 'time' 
                coords=coords)


    elif format == 'yearly':
        # Average by year
        ave = data.groupby('time.year').mean(dim='time')
        
        if use_cftime:
            dates = [cftime.DatetimeGregorian(year, 7, 1, 0, 0, 0, has_year_zero=False) for year in ave['year'].values]

            # create new coordinates ( space unchanged)
            coords = {"time": dates}
            for dim in data.coords:
                if dim not in coords:
                    coords[dim] = data[dim]
            
            # combine all in a new array
            ave = xr.DataArray(
                data=ave, 
                dims=["time"] + [dim for dim in ave.dims if dim != "year"], # replace 'year' with 'time' 
                coords=coords
            )


    elif format == 'seasons':
        # Average by seasons over years        
        ave = data.groupby(['time.year', 'time.season']).mean(dim='time')

        if use_cftime:
            season_times = []
            for (year, season), group in data.groupby(['time.year', 'time.season']):            
                center_time = group['time'].mean()
                season_times.append(center_time.item())
            season_times = xr.DataArray(season_times, dims=['time'], name='time', coords={'time': season_times})
            ave = ave.stack(time=("year", "season"))
            ave = ave.drop_vars(['year','season'])

    elif format in season_months:
        # Average by a specific season (e.g., 'winter', 'summer', etc.) yearly
        season = format.lower()
        if season not in season_months:
            raise ValueError(f"Invalid season specified. Choose from: {', '.join(season_months.keys())}.")
        
        # Filter data by the months corresponding to the season
        ave = data.sel(time=data['time.month'].isin(season_months[season])).mean(dim='time')
        
        if use_cftime:
            last_year = data['time.year'].values[-1]
            dates = [cftime.DatetimeGregorian(last_year, month, 1, 0, 0, 0, has_year_zero=False) for month in season_months[season]]
            ave = xr.DataArray(data=ave, dims=["time"], coords={"time": dates})

    else:
        raise ValueError("Invalid format specified. Choose from: 'plain', 'global', 'monthly', 'seasonally', 'yearly', 'seasons', or a specific season like 'winter', 'spring', 'summer', 'autumn'.")

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


def apply_cost_function(data, data_ref, metric, format='plain', format_ref='global'):
    """
    Apply a cost function to data based on formats.

    Args:
        data (xarray.DataArray): The current dataset.
        data_ref (xarray.DataArray): The reference dataset.
        metric (str): The metric used to compute the cost.b
        format (str, optional): Time format of the current dataset ['plain', 'monthly', 'seasonally', 'yearly', 'global'].
        format_ref (str, optional): Time format of the reference dataset.

    Returns:
        xarray.DataArray: Data containing the computed cost metrics.
    """

    if format_ref == 'global': 
        cdata = cost(data, data_ref, metric)

    elif format == format_ref:
        cdata = cost(data, data_ref, metric)

    elif (format == 'monthly' and format_ref == 'seasonally'):
        cdata = cost(data, data_ref, metric)

    elif format == 'plain':

        if format_ref in ['monthly', 'seasonally']:
            n_years = int(data['time'].size/12)
            start_year = data['time.year'][-1]
            varname = list(data.data_vars)[0]
            data_ref_repeated = np.tile(data_ref[varname].values, n_years)
            data_ref_new = xr.Dataset({varname: (["time"], data_ref_repeated)}, coords={"time": data['time']})
            cdata = cost(data, data_ref_new, metric)

        elif format_ref == 'yearly':
            if (data['time'].size/12 == data_ref['time'].size):
                n_years = data_ref["time"].size
                start_year = int(data_ref["time.year"][0])
                varname = list(data.data_vars)[0]
                data_ref_repeated = np.repeat(data_ref[varname].values, 12)
                data_ref_new = xr.Dataset({varname: (["time"], data_ref_repeated)}, coords={"time": data['time']})
                cdata = cost(data, data_ref_new, metric)
            else:
                raise ValueError("data and data_ref have different sizes.")
        
    else:
        raise ValueError(f"Wrong combination of {format} and {format_ref}")

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
