#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for timeseries

Author: Alessandro Sozza, Paolo Davini (CNR-ISAC) 
Date: Mar 2024
"""

import numpy as np
import xarray as xr
import dask
import cftime
#import nc_time_axis
import matplotlib.pyplot as plt

from osprey.utils.time import get_decimal_year
from osprey.utils.vardict import vardict
from osprey.means.means import cost, movave
from osprey.means.means import spacemean, timemean
from osprey.actions.reader import reader_nemo
from osprey.actions.post_reader import postreader_averaged

def timeseries(expname, 
               startyear, endyear, 
               varname, 
               cost_value=1, 
               offset=0, 
               color=None, 
               rescaled=False, 
               reader_type="nemo", 
               cost_type="norm", 
               average_type="moving", 
               subregion=None): 
    """ 
    Graphics of timeseries 
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varname: variable name
    cost_value: ?
    offset: time offset
    color: curve color
    rescaled: rescale timeseries by the initial value at time=0
    reader_type: read the original raw data or averaged data [nemo, post]
    cost_type: choose the type of cost function [norm, diff, rdiff, abs, rel, var, rvar] 
    subregion: consider a subregion of the water column [mixed-layer, pycnocline, abyss]
    
    """
    
    # reading data
    if reader_type == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)
    elif reader_type == "post":
        data = postreader_averaged(expname, startyear, endyear, varname, 'timeseries')
        tvec = data['time'].values.flatten()

    # fix time-axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # y-axis
    vec = data[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[varname]
        vec = movave(spacemean(data, varname, ndim, subregion),12)
    vec_cutted = vec[6:-6]

    # apply cost function
    vec_cost = cost(vec_cutted, cost_value, cost_type) 

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color

    pp = plt.plot(tvec_offset, vec_cost, **plot_kwargs)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[varname].long_name)

    return pp


def timeseries_diff(expname1, expname2, 
                    startyear, endyear, 
                    var, 
                    offset=0, 
                    color=None,
                    rescaled=False,
                    reader_type="nemo",
                    cost_type="norm", 
                    average_type="moving", 
                    subregion=None): 
    """ Graphics of two-field difference timeseries """
    
    # reading data
    if reader_type == 'nemo':
        data1 = reader_nemo(expname1, startyear, endyear)
        data2 = reader_nemo(expname2, startyear, endyear)
        tvec = get_decimal_year(data1['time'].values)
    elif reader_type == 'averaged':
        data1 = postreader_averaged(expname1, startyear, endyear, var, 'series')
        data2 = postreader_averaged(expname2, startyear, endyear, var, 'series')        
        tvec = data1['time'].values.flatten()

    # fix time axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # fix y-axis
    vec1 = data1[var].values.flatten()
    vec2 = data1[var].values.flatten()
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec1 = movave(spacemean(data1, var, ndim, subregion),12)
        vec2 = movave(spacemean(data2, var, ndim, subregion),12)
    vec1_cutted = vec1[6:-6]
    vec2_cutted = vec2[6:-6]
    vec_cost = cost(vec1_cutted, vec2_cutted, cost_type)

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color
    
    pp = plt.plot(tvec_offset, vec_cost, **plot_kwargs)
    plt.xlabel(data1['time'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp


def timeseries_diff_mf(expname1, startyear1, endyear1, 
                       expname2, startyear2, endyear2, 
                       var, 
                       offset=0, 
                       color=None, rescaled=False, 
                       reader_type="nemo", cost_type="norm", 
                       average_type="moving", subregion=None): 
    """ Graphics of mean-field difference timeseries """
    
    # procedure: expname2 is time-averaged to obtain a spatial-only meanfield

    # reading data
    if reader_type == 'nemo':
        data1 = reader_nemo(expname1, startyear1, endyear1)
        data2 = reader_nemo(expname2, startyear2, endyear2)
        tvec = get_decimal_year(data1['time'].values)
    elif reader_type == 'averaged':
        data1 = postreader_averaged(expname1, startyear1, endyear1, var, 'series')
        data2 = postreader_averaged(expname2, startyear2, endyear2, var, 'series')        
        tvec = data1['time'].values.flatten()

    # time mean of expname2
    meanfld = timemean(data2, var)
    fdata = cost(data1, meanfld, cost_type)
    fdata.attrs['name'] = data1.attrs['name']

    # fix time axis
    tvec_cutted = tvec[6:-6]
    tvec_offset = [tvec_cutted[i]+offset for i in range(len(tvec_cutted))]

    # select y-axis
    vec_cost = fdata[var].values.flatten()    
    if average_type == 'moving':
        ndim = vardict('nemo')[var]
        vec_cost = movave(spacemean(fdata, var, ndim, subregion),12)

    # apply rescaling
    if rescaled == True:
        vec_cost = vec_cost/vec_cost[0]
    
    # fix y-axis
    vec_cutted = vec_cost[6:-6]

    # plot
    plot_kwargs = {}
    if color is not None:
        plot_kwargs['color'] = color
    
    pp = plt.plot(tvec_offset, vec_cutted, **plot_kwargs)
    plt.xlabel(data1['time'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp