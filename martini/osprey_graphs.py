#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for graphics

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import os
import numpy as np
import xarray as xr
import dask
import cftime
import nc_time_axis
import matplotlib.pyplot as plt
import osprey_tools as ost
import osprey_io as osi
import osprey_means as osm


##########################################################################################
# STANDARD PLOTS

def timeseries(expname, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset, color):
    """ graphics of timeseries """

    isub = False
    if '-' in var:
        isub = True

    # read (or create) averaged data
    data = osi.read_averaged_timeseries_T(expname, startyear, endyear, var, ndim, isub)
    # assembly and plot
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(data[var].values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, osm.cost(vv1, norm, idx_norm), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp


def gregoryplot(expname, startyear, endyear, var_x, ndim_x, var_y, ndim_y, idx_ave, color):
    """ graphics of gregory plot"""

    isub_x = False
    if '-' in var_x:
        isub_x = True

    isub_y = False
    if '-' in var_x:
        isub_y = True

    xdata = osi.read_averaged_timeseries_T(expname, startyear, endyear, var_x, ndim_x, isub_x)
    ydata = osi.read_averaged_timeseries_T(expname, startyear, endyear, var_y, ndim_y, isub_y)
    tt = xdata['time'].values.flatten()
    if idx_ave == 'ave':
        vx = xdata[var_x].values.flatten()
        vy = ydata[var_y].values.flatten()
        vx1 = vx; vy1 = vy; tt1 = tt
    elif idx_ave == 'mave':
        vx = osm.movave(xdata[var_x].values.flatten(),12)
        vy = osm.movave(ydata[var_y].values.flatten(),12)        
        vx1 = vx[6:-6]; vy1 = vy[6:-6]; tt1 = tt[6:-6]
    #colors = [tt1[i] for i in range(len(tt1))]
    pp = plt.plot(vx1, vy1, color) #, c=colors, cmap=plt.cm.coolwarm)        
    plt.xlabel(xdata[var_x].long_name)
    plt.ylabel(ydata[var_y].long_name)
    # cbar = plt.colorbar()
    # cbar.set_label(xdata['time'].long_name, ha='left', labelpad=10)

    return pp


def profile(expname, startyear, endyear, var, norm, idx_norm):
    """ graphics profile """

    data = osi.read_averaged_profile_T(expname, startyear, endyear, var)
    zz = data['z'].values.flatten() 
    vv = data[var].values.flatten()
    pp = plt.plot(osm.cost(vv, norm, idx_norm),zz)
    plt.ylabel(data['z'].long_name)
    plt.xlabel(data[var].long_name)

    return pp


def hovmoller(expname, startyear, endyear, var, x_axis, y_axis, idx_norm):
    """ graphics of hovmöller diagram """

    data = osi.read_averaged_map_T(expname, startyear, endyear, var)
    # pp = plt.plot(x=x_axis, y=y_axis, c=var, cmap=plt.cm.coolwarm)
    #plt.xlabel(data['time'].long_name)
    #plt.ylabel(data['z'].long_name)
    #x = data[x_axis].values.flatten()
    #y = data[y_axis].values.flatten()
    #c = data[var].values.flatten().reshape(len(y),len(x))
    #pp = plt.pcolormesh(x, y, c)
    delta = (data[var] - data[var].isel(time=0))
    pp = delta.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.ylim(-5000,0)

    return pp


##########################################################################################
# TWO-FIELD DIFFERENCE (within the same temporal window)

def timeseries_diff(exp1, exp2, startyear, endyear, var, ndim, norm, idx_norm, idx_ave, offset):
    """ graphics of timeseries of two-field difference """

    isub = False
    if '-' in var:
        isub = True
        
    # read (or create) averaged data 
    data1 = osi.read_averaged_timeseries_T(exp1, startyear, endyear, var, ndim, isub)
    data2 = osi.read_averaged_timeseries_T(exp2, startyear, endyear, var, ndim, isub)
    # assembly and plot
    tt = data1['time'].values.flatten()
    delta = data2[var]-data1[var]
    if idx_ave == 'ave':
        vv = delta.values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(delta.values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2,osm.cost(vv1, norm, idx_norm))
    plt.xlabel(data1['time'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp


def profiles_diff(exp1, exp2, startyear, endyear, var, norm, idx_norm):
    """ graphics of profile difference """

    data1 = osi.read_averaged_profile_T(exp1, startyear, endyear, var)
    data2 = osi.read_averaged_profile_T(exp2, startyear, endyear, var)
    delta = data2[var]-data1[var]
    zz = data1['z'].values.flatten()     
    vv = delta.values.flatten()
    pp = plt.plot(osm.cost(vv, norm, idx_norm),zz)
    plt.xlabel(data1['z'].long_name)
    plt.ylabel(data1[var].long_name)

    return pp


##########################################################################################
# ANOMALY PLOTS (with respect to a mean field)

def timeseries_diff2(expname, startyear, endyear, refname, startref, endref, var, ndim, idx_norm, idx_ave, offset, color):

    isub = False
    if '-' in var:
        isub = True

    # read (or create) averaged data 
    data = osi.read_averaged_timeseries_T(expname, startyear, endyear, var, ndim, isub)    
    mdata = osi.read_averaged_field_T(refname, startref, endref, var, ndim)

    # assembly and plot
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        vm = osm.spacemean(expname, mdata[var], ndim)
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(data[var].values.flatten(),12)
        vm = osm.spacemean(expname, mdata[var], ndim)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, osm.cost(vv1, vm, idx_norm), color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel('Cost function')

    return pp


def timeseries_anomaly(expname, startyear, endyear, refname, startref, endref, var, ndim, idx_ave, offset, color):

    data = osi.read_averaged_timeseries_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var, ndim)
    tt = data['time'].values.flatten()
    if idx_ave == 'ave':
        vv = data[var].values.flatten()
        tt1 = tt; vv1 = vv
    elif idx_ave == 'mave':
        vv = osm.movave(data[var].values.flatten(),12)
        tt1 = tt[6:-6]; vv1 = vv[6:-6]
    tt2 = [tt1[i]+offset for i in range(len(tt1))]
    pp = plt.plot(tt2, vv1, color)
    plt.xlabel(data['time'].long_name)
    plt.ylabel(data[var].long_name)

    return pp

def hovmoller_anomaly(expname, startyear, endyear, refname, startref, endref, var):

    data = osi.read_averaged_hovmoller_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var)    
    delta = data[var]#/data[var].isel(time=0)-1
    pp = delta.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.ylim(-5000,0)

    return pp
