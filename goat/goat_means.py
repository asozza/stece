#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
  ____   ____     _   _____
 / __/  / __ \   / \ |_   _|
| |  _ | |  | | / _ \  | |  
| |_| || |  | |/ /__ \ | |  
 \____| \____//_/   \_\|_|  

GOAT library for averaging operations and other means

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import os
import numpy as np
import xarray as xr
import cftime
import pandas as pd
from sklearn.linear_model import LinearRegression
import goat_tools as gt
import goat_io as io

# define differential forms for integrals
def elements(expname):
    """ define differential forms for integrals """

    df = {}
    domain = io.read_domain(expname=expname)
    df['vol'] = domain['e1t']*domain['e2t']*domain['e3t_0']
    df['area'] = domain['e1t']*domain['e2t']
    df['dx'] = domain['e1t']
    df['dy'] = domain['e2t']
    df['dz'] = domain['e3t_0']

    return df

# interpolated moving average
def intave(xdata, ydata, N):

    data = io.read_T(expname=expname, year=year)
    delta = gt.cost(data, field, idx)

    return delta

#def linear_fit(x, y):
#    """ linear fit """
#    ya = [[y[i]] for i in range(len(y))]
#    xa = [[x[i]] for i in range(len(x))]
#    model=LinearRegression()
#    model.fit(xa, ya)
#    mp = model.coef_[0][0]
#    qp = model.intercept_[0]
#    return mp,qp

##################################################################################
# AVERAGES

# moving/running average
def movave(ydata, N):
    """ moving average """

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
# AVERAGING OPERATIONS ON A FIELD

# Definitions: 
# global_mean: time and space average
# time_mean: average on time 
# space_mean:  spatial average on x,y,z or x,y weighted by volume or area

def timemean(data, var):
    """ Time average of a field """

    ave = data[var].mean(dim=['time']).values

    return ave

def globalmean(data, var, ndim, subreg = None):
    """ Global average of a field """

    expname = gt.get_expname(data)
    df = elements(expname)
    if ndim == '3D':
        ave = data[var].weighted(df['vol']).mean(dim=['time', 'z', 'y', 'x']).values
        if subreg != None:
            z1,z2 = gt.subrange(subreg)
            subvol = df['vol'].isel(z=slice(z1,z2))
            subvar = data[var].isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['time', 'z', 'y', 'x']).values
    elif ndim == '2D':
        ave = data[var].weighted(df['area']).mean(dim=['time', 'y', 'x']).values
    else:
        raise ValueError(" Invalid dimensions ")

    return ave

def spacemean(data, var, ndim, subreg = None):
    """ Spatial average of a field """

    expname = gt.get_expname(data)
    df = elements(expname) 
    if ndim == '3D':
        ave = data[var].weighted(df['vol']).mean(dim=['z', 'y', 'x']).values
        if subreg != None:
            z1,z2 = gt.subrange(subreg,'ORCA2')
            subvol = df['vol'].isel(z=slice(z1,z2))
            subvar = data[var].isel(z=slice(z1,z2))
            ave = subvar.weighted(subvol).mean(dim=['z', 'y', 'x']).values
    elif ndim == '2D':
        ave = data[var].weighted(df['area']).mean(dim=['y', 'x']).values
    else:
        raise ValueError(" Invalid dimensions ")

    return ave

#################################################################################
