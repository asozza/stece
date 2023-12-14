#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GOAT library for plots

Authors
Alessandro Sozza (CNR-ISAC, Dec 2023)
"""

import os
import xarray as xr
import matplotlib.pyplot as plt
import goat_tools as gt
import goat_io as io
import goat_means as gm


# time series
def plot_ts_ma3d(expname, startyear, endyear, var):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    pp = plt.plot(tt,vv)

    return pp

def plot_ts_ma2d(expname, startyear, endyear, var):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['area']).mean(dim=['y', 'x']).values.flatten(),12)
    pp = plt.plot(tt,vv)

    return pp

def plot_ts_ma3d_sub(expname, startyear, endyear, var, z1, z2, norm):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    subvol = df['vol'].isel(z=slice(z1,z2))
    subvar = data[var].isel(z=slice(z1,z2))
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(subvar.weighted(subvol).mean(dim=['z', 'y', 'x']).values.flatten(),12)/norm    
    pp = plt.plot(tt,vv)

    return pp

def plot_ts_ra3d(expname, startyear, endyear, var):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    rr = gm.runave(vv)
    pp = plt.plot(tt,rr)

    return pp

def plot_ts_ra2d(expname, startyear, endyear, var):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tt = gt.dateDecimal(data['time'].values)
    vv = gm.movave(data[var].weighted(df['area']).mean(dim=['y', 'x']).values.flatten(),12)
    rr = gm.runave(vv)
    pp = plt.plot(tt,rr)

    return pp

def gregory_plot_ma3d(expname, startyear, endyear, var1, var2):
    
    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    tf = len(data['time'].values) 
    vv1 = gm.movave(data[var1].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    vv2 = gm.movave(data[var2].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values.flatten(),12)
    pp = plt.plot(vv1[6:tf-6],vv2[6:tf-6])

    return pp


# profiles
def plot_prof(expname, startyear, endyear, var):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    zz = data['z'].values.flatten()
    vv = data[var].weighted(df['area']).mean(dim=['time', 'y', 'x']).values.flatten()
    pp = plt.plot(vv,zz)

    return pp


# maps and density plots
def map2d(expname, year, month, var, Tmin, Tmax):

    data = io.read_T(expname=expname, year=year)
    if Tmin == Tmax:
        pp = data[var].isel(time=month-1).plot()
    else:
        pp = data[var].isel(time=month-1).plot(vmin=Tmin, vmax=Tmax)
    
    return pp

def map2d_anomaly(expname, year, month, var1, var2, Tmin, Tmax):

    data = io.read_T(expname=expname, year=year)
    delta = xr.where(data[var1]!=0, data[var2].values-data[var1].values, 0.0)
    pp = delta.isel(time=month-1).plot(vmin=Tmin, vmax=Tmax)
    if Tmin == Tmax:
        pp = delta.isel(time=month-1).plot()
    else:
        pp = delta.isel(time=month-1).plot(vmin=Tmin, vmax=Tmax)
    
    return pp

def plot_hovmoller(expname, startyear, endyear, var):

    data = io.readmf_T(expname=expname, startyear=startyear, endyear=endyear)
    df = gm.elements(expname=expname)
    hovm = data[var].weighted(df['area']).mean(dim=['y', 'x'])    
    pp = hovm.plot(y='z', ylim=(-5000, 0))
    
    return pp