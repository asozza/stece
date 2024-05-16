#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GOAT: Global Ocean & Atmosphere Trends
------------------------------------------------------
GOAT library for averaging operations and other means

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import os
import numpy as np
import xarray as xr
import cftime
import dask
from sklearn.linear_model import LinearRegression
import goat_tools as gt
import goat_io as io

# define differential forms for integrals
def elements(expname):

    df = {}
    domain = io.read_domain(expname=expname)
    df['vol'] = domain['e1t']*domain['e2t']*domain['e3t_0']
    df['area'] = domain['e1t']*domain['e2t']
    df['dx'] = domain['e1t']
    df['dy'] = domain['e2t']
    df['dz'] = domain['e3t_0']

    return df

def local_cost_function(expname, year, field, idx):
    
    data = io.read_T(expname=expname, year=year)
    delta = gt.cost(data, field, idx)

    return delta

# linear fit
def linear_fit(x, y):

    ya = [[y[i]] for i in range(len(y))]
    xa = [[x[i]] for i in range(len(x))]
    model=LinearRegression()
    model.fit(xa, ya)
    mp = model.coef_[0][0]
    qp = model.intercept_[0]

    return mp,qp

##################################################################
# AVERAGES

# interpolated moving average
def intave(xdata, ydata, N):

    x_orig = np.array(gt.dateDecimal(xdata.values))

    for i in range(N):    
        x_filled = np.array(gt.dateDecimal(xdata.where(xdata['time.month']==i+1,drop=True).values))
        y_filled = np.array(ydata.where(xdata['time.month']==i+1,drop=True).values.flatten())
        if (i==0):
            y_smooth = np.interp(x_orig, x_filled, y_filled)/N
        else:
            y_smooth += np.interp(x_orig, x_filled, y_filled)/N
    
    return y_smooth

# moving/running average
def movave(ydata, N):

    #y_list = np.array(ydata.values.flatten())
    y_padded = np.pad(ydata, (N//2, N-1-N//2), mode='edge')
    y_smooth = np.convolve(y_padded, np.ones((N,))/N, mode='valid')

    return y_smooth

# cumulative average
def cumave(ydata):
        
    ave = np.cumsum(ydata)
    for i in range(1,len(ydata)):
        ave[i] = ave[i]/(i+1)

    return ave

#################################################################################
# MEAN OPERATIONS ON THE FIELD

# Definitions: 
# global_mean: time and space average
# time_mean: average on time 
# space_mean:  spatial average on x,y,z or x,y weighted by volume or area
# sub: spatial average on a subinterval z in [z1,z2]
# suball: according to subregions

# global average over space and time
def timemean(field):
    
    meanfield = field.mean(dim=['time']).values

    return meanfield

def globalmean3d(expname, field):

    df = elements(expname=expname)   
    ave = field.weighted(df['vol']).mean(dim=['time', 'z', 'y', 'x']).values

    return ave

def globalmean3d_sub(expname, field, z1, z2):

    df = elements(expname=expname)           
    subvol = df['vol'].isel(z=slice(z1,z2))
    subvar = field.isel(z=slice(z1,z2))
    ave = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x']).values

    return ave

def globalmean3d_suball(expname, field):

    ave = []
    df = elements(expname=expname)           
    z1,z2 = gt.subregions('ORCA2')
    for i in range(3):
        subvol = df['vol'].isel(z=slice(z1[i],z2[i]))
        subvar = field.isel(z=slice(z1[i],z2[i]))
        ave[i] = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x']).values

    return ave

def globalmean2d(expname, field):

    df = elements(expname=expname)   
    ave = field.weighted(df['area']).mean(dim=['time', 'y', 'x']).values

    return ave

def spacemean3d(expname, field):

    df = elements(expname=expname)       
    ave = field.weighted(df['vol']).mean(dim=['z', 'y', 'x']).values

    return ave

def spacemean3d_sub(expname, field, z1, z2):

    df = elements(expname=expname)           
    subvol = df['vol'].isel(z=slice(z1,z2))
    subvar = field.isel(z=slice(z1,z2))    
    ave = subvar.weighted(subvol).mean(dim=['z', 'y', 'x']).values

    return ave

def spacemean3d_suball(expname, field):

    ave = []
    df = elements(expname=expname)
    z1,z2 = gt.subregions('ORCA2')
    for i in range(3):
        subvol = df['vol'].isel(z=slice(z1[i],z2[i]))
        subvar = field.isel(z=slice(z1[i],z2[i]))
        ave.append(subvar.weighted(subvol).mean(dim=['z', 'y', 'x']).values)

    return ave

def spacemean2d(expname, field):

    df = elements(expname=expname)
    ave = field.weighted(df['area']).mean(dim=['y', 'x']).values

    return ave

#################################################################################
# new functions:

def globalmean(expname, field, ndim):

    df = elements(expname=expname) 
    if ndim == '3D':  
        ave = field.weighted(df['vol']).mean(dim=['time', 'z', 'y', 'x']).values
    elif ndim == '2D':
        ave = field.weighted(df['area']).mean(dim=['time', 'y', 'x']).values
    else:        
        raise ValueError(" ndim =! (2,3): Check dimensions! ")

    return ave

def spacemean(expname, field, ndim):

    df = elements(expname=expname) 
    if ndim == '3D':  
        ave = field.weighted(df['vol']).mean(dim=['z', 'y', 'x']).values
    elif ndim == '2D':
        ave = field.weighted(df['area']).mean(dim=['y', 'x']).values
    else:        
        raise ValueError(" ndim =! (2,3): Check dimensions! ")

    return ave

def cost_field(data, mdata, var, ndim):

    xdata=data[var]-mdata[var]

    return xdata