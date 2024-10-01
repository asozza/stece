#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for timeseries

Author: Alessandro Sozza (CNR-ISAC) 
Date: Mar 2024
"""

import os
import numpy as np
import xarray as xr
import dask
import yaml
import cftime
import matplotlib.pyplot as plt

from osprey.utils.folders import paths
from osprey.utils.time import get_decimal_year
from osprey.utils.vardict import vardict
from osprey.means.means import cost, movave
from osprey.means.means import spacemean, year_shift
from osprey.actions.reader import reader_nemo
from osprey.actions.postreader import postreader_nemo, reader_meanfield

def _cutted(vec):
    """ Cut vector """
    return vec[6:-6]

def _rescaled(vec):
    """ rescale by the initial value """
    return vec/vec[0]

def timeseries(expname, startyear, endyear, varlabel, 
               reader="nemo", metric="base", replace=False, 
               rescale=False, avetype="standard", timeoff=0, 
               color=None, linestyle='-', marker=None, label=None, ax=None, figname=None):
    """ 
    Graphics of timeseries 
    
    Positional Args:
    - expname: experiment name
    - startyear,endyear: time window
    - varlabel: variable label (varname + ztag)

    Optional Args:
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    - replace: replace existing files [False or True]
    
    Optional Args for figure settings:
    - rescale: rescale by initial value
    - avetype: choose the type of average ['moving' or 'standard']
    - timeoff: time offset    
    - color, linestyle, marker, label: plot attributes
    - ax: plot axes
    - figname: save plot to file

    """
    
    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname, ztag = varlabel, None

    info = vardict('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":
        data = reader_nemo(expname, startyear, endyear)
        tvec = get_decimal_year(data['time'].values)

        # apply cost function
        if metric != 'base':
            mean_data = reader_meanfield(varname=varname)
            data = cost(data, mean_data, metric)

        # apply moving average (if needed)
        if avetype == 'moving':       
            vec = movave(spacemean(data, varname, info['dim'], ztag),12)                
            tvec, vec = _cutted(tvec), _cutted(vec)
        else:
            vec = spacemean(data, varname, info['dim'], ztag)

    # Read post-processed data
    elif reader == "post":
        data = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, 
                               varlabel=varlabel, diagname='timeseries', 
                               replace=replace, metric=metric)
        tvec = data['time'].values.flatten()

        # apply moving average
        if avetype == 'moving':
            vec = movave(data[varlabel],12)
            tvec, vec = _cutted(tvec), _cutted(vec)
        else:
            vec = data[varlabel].values.flatten()

    # add time offset
    if timeoff > 0:
        tvec = [time + timeoff for time in tvec]

    # apply rescaling
    if rescale:
        vec = _rescaled(vec)

    # load plot features
    plot_kwargs = {}
    if color:
        plot_kwargs['color'] = color
    if linestyle:
        plot_kwargs['linestyle'] = linestyle
    if marker:
        plot_kwargs['marker'] = marker
    if label:
        plot_kwargs['label'] = label

    # If an axis is provided, plot on it; otherwise, plot on the default plt object
    if ax is not None:
        pp = ax.plot(tvec, vec, **plot_kwargs)
        ax.set_xlabel('time')
        ax.set_ylabel(info['long_name'])  # Use a generic label or info from your dataset
    else:
        pp = plt.plot(tvec, vec, **plot_kwargs)
        plt.xlabel('time')
        plt.ylabel(info['long_name'])

    # Save figure
    if figname:
        dirs = paths()
        plt.savefig(os.path.join(dirs['osprey'], figname))

    return pp


def timeseries_two(expname1, expname2, startyear, endyear, varlabel, 
               reader="post", metric="base", replace=False, 
               rescale=False, avetype="moving", timeoff=0, 
               color=None, figname=None):
    """ 
    Graphics of two-experiment timeseries distance based on a metric
    
    Positional Args:
    - expname1,expname2: experiment names
    - startyear,endyear: time window
    - varlabel: variable label (varname + ztag)

    Optional Args:
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - metric: choose the type of cost function ['base', 'norm', 'diff' ...]
    - replace: replace existing files [False or True]
    
    Optional Args for figure settings:
    - rescale: rescale by initial value
    - avetype: choose the type of average ['moving' or 'standard']
    - timeoff: time offset    
    - color: curve color
    - figname: save plot to file
    
    """
    
    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname, ztag = varlabel, None

    info = vardict('nemo')[varname]

    # read data from raw NEMO output
    if reader == 'nemo':
        data1 = reader_nemo(expname1, startyear, endyear)
        data2 = reader_nemo(expname2, startyear, endyear)
        tvec = get_decimal_year(data1['time'].values)

        # apply moving average
        if avetype == 'moving':
            vec1 = movave(spacemean(data1, varname, info['dim'], ztag),12)
            vec2 = movave(spacemean(data2, varname, info['dim'], ztag),12)
        else:
            vec1 = data1[varname].values.flatten()
            vec2 = data2[varname].values.flatten()

    # read post-processed data
    elif reader == 'post':
        data1 = postreader_nemo(expname=expname1, startyear=startyear, endyear=endyear, varlabel=varlabel, 
                                diagname='timeseries', replace=replace, metric='base')
        data2 = postreader_nemo(expname=expname2, startyear=startyear, endyear=endyear, varlabel=varlabel, 
                                diagname='timeseries', replace=replace, metric='base')
        tvec = data1['time'].values.flatten()

        # apply moving average
        if avetype == 'moving':
            vec1 = movave(data1[varlabel],12)
            vec2 = movave(data2[varlabel],12)
        else:
            vec1 =data1[varlabel].values.flatten()
            vec2 =data2[varlabel].values.flatten()

    # apply cost function
    if metric != 'base':
        vec = cost(vec1, vec2, metric)
    else:
        raise ValueError("The metric cannot be 'base' when calculating the distance between experiments.")

    # cut vectors if moving average is chosen
    if avetype == 'moving':
        tvec, vec = _cutted(tvec), _cutted(vec)

    # add time offset
    if timeoff > 0:
        tvec = [time + timeoff for time in tvec]

    # apply rescaling
    if rescale:
        vec = _rescaled(vec)

    # plot timeseries
    plot_kwargs = {'color': color} if color else {}
    pp = plt.plot(tvec, vec, **plot_kwargs)
    plt.xlabel('time')
    plt.ylabel(info['long_name'])

    # Save figure
    if figname:
        dirs = paths()
        plt.savefig(os.path.join(dirs['osprey'], figname))



    return pp
 

def timeseries_yearshift(expname1, startyear1, endyear1, expname2, startyear2, endyear2, varlabel, shift_threshold, 
                         reader="nemo", replace=False, avetype="standard", timeoff=0, 
                         color=None, linestyle='-', marker=None, label=None, ax=None, figname=None):
    """ 
    Graphics of year-shift timeseries 
    
    Positional Args:
    - expname1,2: experiment names
    - startyear,endyear: time window
    - varlabel: variable label (varname + ztag)

    Optional Args:
    - reader: read the original raw data or averaged data ['nemo', 'post']
    - replace: replace existing files [False or True]
    
    Optional Args for figure settings:
    - avetype: choose the type of average ['moving' or 'standard']
    - timeoff: time offset    
    - color, linestyle, marker, label: plot attributes
    - ax: plot axes
    - figname: save plot to file

    """
    
    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname, ztag = varlabel, None

    info = vardict('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":
        data1 = reader_nemo(expname1, startyear1, endyear1)
        data2 = reader_nemo(expname2, startyear2, endyear2)        

        tvec1 = get_decimal_year(data1['time'].values)
        tvec2 = get_decimal_year(data2['time'].values)

        # apply moving average (if needed)
        if avetype == 'moving':
            vec1 = movave(spacemean(data1, varname, info['dim'], ztag),12)
            tvec1, vec1 = _cutted(tvec1), _cutted(vec1)
            vec2 = movave(spacemean(data2, varname, info['dim'], ztag),12)
            tvec2, vec2 = _cutted(tvec2), _cutted(vec2)
        else:
            vec1 = spacemean(data1, varname, info['dim'], ztag)
            vec2 = spacemean(data2, varname, info['dim'], ztag)

    # Read post-processed data
    elif reader == "post":
        data1 = postreader_nemo(expname=expname1, startyear=startyear1, endyear=endyear1, varlabel=varlabel, diagname='timeseries', replace=replace, metric='base')
        data2 = postreader_nemo(expname=expname2, startyear=startyear2, endyear=endyear2, varlabel=varlabel, diagname='timeseries', replace=replace, metric='base')

        tvec1 = data1['time'].values.flatten()
        tvec2 = data2['time'].values.flatten()

        # apply moving average
        if avetype == 'moving':
            vec1 = movave(data1[varlabel],12)
            tvec1, vec1 = _cutted(tvec1), _cutted(vec1)
            vec2 = movave(data2[varlabel],12)
            tvec2, vec2 = _cutted(tvec2), _cutted(vec2)
        else:
            vec1 = data1[varlabel].values.flatten()
            vec2 = data2[varlabel].values.flatten()

    # compute year-shift
    shift = year_shift(tvec1, vec1, tvec2, vec2, shift_threshold)

    # add time offset
    if timeoff > 0:
        tvec1 = [time + timeoff for time in tvec1]
        tvec2 = [time + timeoff for time in tvec2]

    # load plot features
    plot_kwargs = {}
    if color:
        plot_kwargs['color'] = color
    if linestyle:
        plot_kwargs['linestyle'] = linestyle
    if marker:
        plot_kwargs['marker'] = marker
    if label:
        plot_kwargs['label'] = label

    # If an axis is provided, plot on it; otherwise, plot on the default plt object
    if ax is not None:
        pp = ax.scatter(tvec1, shift, s=2, **plot_kwargs)
        ax.axhline(0, color='gray', linestyle='--')  # Zero reference line
        ax.set_xlabel('time [years]')
        ax.set_ylabel('year shift [years]')  # Use a generic label or info from your dataset
        ax.grid()
    else:
        pp = plt.scatter(tvec1, shift, s=2, **plot_kwargs)
        plt.axhline(0, color='gray', linestyle='--')  # Zero reference line
        plt.xlabel('time [years]')
        plt.ylabel('year shift [years]')
        plt.grid()

    # Save figure
    if figname:
        dirs = paths()
        plt.savefig(os.path.join(dirs['osprey'], figname))

    return pp