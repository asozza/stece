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

from osprey.utils.config import paths
from osprey.utils.time import get_decimal_year
from osprey.utils import catalogue
from osprey.means.means import apply_cost_function, movave
from osprey.means.means import spacemean, timemean, year_shift
from osprey.actions.reader import reader_nemo, reader_nemo_field
from osprey.actions.postreader import postreader_nemo, averaging


def _cutted(vec):
    """ Cut vector """
    return vec[6:-6]

def _rescaled(vec):
    """ rescale by the initial value """
    return vec/vec[0]


def timeseries(expname, startyear, endyear, varlabel, format="plain", 
               reader="post", orca="ORCA2", replace=False, metric="base", refinfo=None, 
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

    info = catalogue.observables('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":

        data = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)        
        data = averaging(data=data, varlabel=varlabel, diagname='timeseries', format=format, orca=orca)
        tvec = get_decimal_year(data['time'].values)

        # apply cost function
        if metric != 'base':

            xdata = reader_nemo_field(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varname=varname)
            xdata = averaging(data=xdata, varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], orca=orca)            

            if refinfo['diagname'] == 'field':
                data = apply_cost_function(data, xdata, metric, format=format, format_ref=refinfo['format'])    
                data = averaging(data=data, varlabel=varlabel, diagname='timeseries', format=format, orca=orca)
            else:
                data = apply_cost_function(data, xdata, metric, format=format, format_ref=refinfo['format'])

    # Read post-processed data
    elif reader == "post":

        data = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, 
                               diagname='timeseries', format=format, orca=orca, replace=replace, metric=metric, refinfo=refinfo)
        tvec = get_decimal_year(data['time'].values)

    # apply moving average
    if (avetype == 'moving' and format == 'plain'):
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


def timeseries_yearshift(expname1, startyear1, endyear1, expname2, startyear2, endyear2, varlabel, shift_threshold, 
                         format='plain', reader="post", orca="ORCA2", replace=False, avetype="standard", timeoff=0, 
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

    info = catalogue.observables('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":

        data1 = reader_nemo_field(expname=expname1, startyear=startyear1, endyear=endyear1, varname=varname)        
        data1 = averaging(data=data1, varlabel=varlabel, diagname='timeseries', format=format, orca=orca)
        tvec1 = get_decimal_year(data1['time'].values)

        data2 = reader_nemo_field(expname=expname2, startyear=startyear2, endyear=endyear2, varname=varname)        
        data2 = averaging(data=data2, varlabel=varlabel, diagname='timeseries', format=format, orca=orca)
        tvec2 = get_decimal_year(data2['time'].values)

    # Read post-processed data
    elif reader == "post":

        data1 = postreader_nemo(expname=expname1, startyear=startyear1, endyear=endyear1, varlabel=varlabel, 
                               diagname='timeseries', format=format, orca=orca, replace=replace, metric='base', refinfo=None)
        tvec1 = get_decimal_year(data1['time'].values)

        data2 = postreader_nemo(expname=expname2, startyear=startyear2, endyear=endyear2, varlabel=varlabel, 
                               diagname='timeseries', format=format, orca=orca, replace=replace, metric='base', refinfo=None)
        tvec2 = get_decimal_year(data2['time'].values)

        # apply moving average
        if avetype == 'moving':
            vec1 = movave(data1[varlabel],12)
            tvec1, vec1 = _cutted(tvec1), _cutted(vec1)
            vec2 = movave(data2[varlabel],12)
            tvec2, vec2 = _cutted(tvec2), _cutted(vec2)
        else:
            vec1 = data1[varlabel].values
            vec2 = data2[varlabel].values

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


def timeseries_yearshift_mean(expname1, startyear1, endyear1, expname2, startyear2, endyear2, varlabel, shift_threshold, 
                              reader="nemo", replace=False, avetype="standard", timeoff=0, residue=False,
                              color=None, marker=None, label=None, ax=None, figname=None):
    """ 
    Data for timeseries mean year-shift & residue
    
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

    info = catalogue.observables('nemo')[varname]

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

    # chunk averaging 
    step_size = 121
    mean_shift = [np.mean(shift[i:i + step_size]) for i in range(0, len(shift), step_size)]
    mean_time = [int(np.mean(tvec1[i:i + step_size])) for i in range(0, len(tvec1), step_size)]
    linear_shift = [mean_time[i]-1995 for i in range(0, len(mean_time))]
    delta_shift = [mean_shift[i]-linear_shift[i] for i in range(0, len(mean_shift))]

    # load plot features
    plot_kwargs = {}
    if color:
        plot_kwargs['color'] = color
    if marker:
        plot_kwargs['marker'] = marker
    if label:
        plot_kwargs['label'] = label

    # If an axis is provided, plot on it; otherwise, plot on the default plt object
    if ax is not None:
        if residue is False:
            pp = ax.scatter(mean_time, mean_shift, **plot_kwargs)
        else:
            pp = ax.scatter(mean_time, delta_shift, **plot_kwargs)
        ax.axhline(0, color='gray', linestyle='--')  # Zero reference line
        ax.set_xlabel('time [years]')
        ax.set_ylabel('year shift [years]')  # Use a generic label or info from your dataset
        ax.grid()
    else:
        if residue is False:
            pp = plt.scatter(mean_time, mean_shift, **plot_kwargs)
        else:
            pp = plt.scatter(mean_time, delta_shift, **plot_kwargs)
        plt.axhline(0, color='gray', linestyle='--')  # Zero reference line
        plt.xlabel('time [years]')
        plt.ylabel('year shift [years]')
        plt.grid()

    # Save figure
    if figname:
        dirs = paths()
        plt.savefig(os.path.join(dirs['osprey'], figname))

    return pp


def timeseries_with_markers(expname, startyear, endyear, varlabel, format="plain", 
               reader="post", orca="ORCA2", replace=False, metric="base", refinfo=None, 
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

    info = catalogue.observables('nemo')[varname]

    # Read data from raw NEMO output
    if reader == "nemo":

        data = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)        
        data = averaging(data=data, varlabel=varlabel, diagname='timeseries', format=format, orca=orca)
        tvec = get_decimal_year(data['time'].values)

    # Read post-processed data
    elif reader == "post":

        data = postreader_nemo(expname=expname, startyear=startyear, endyear=endyear, 
                               varlabel=varlabel, diagname='timeseries', replace=replace, metric=metric)
        tvec = data['time'].values

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

    # markers
    years_interval = 120 # number of months x years of one chunk
    time_indices = np.arange(0, len(tvec), years_interval)    
    vec1_markers = tvec[time_indices]
    vec2_markers = vec[time_indices]

    # plot
    plot_kwargs = {}
    if color:
        plot_kwargs['color'] = color
    if linestyle:
        plot_kwargs['linestyle'] = linestyle
    if label:
        plot_kwargs['label'] = label

    scatter_kwargs = {}
    if color:
        scatter_kwargs['color'] = color
    if marker:
        scatter_kwargs['marker'] = marker

    fig = plt.subplot()

    plt.plot(tvec, vec, **plot_kwargs)
    plt.scatter(vec1_markers, vec2_markers, zorder=10, edgecolor='black', label='_nolegend_', **scatter_kwargs)

    # Set labels, example labels here
    plt.xlabel('time')
    plt.ylabel(info['long_name'])
    
    # Save figure
    if figname:
        dirs = paths()
        plt.savefig(os.path.join(dirs['osprey'], figname))

    return fig
