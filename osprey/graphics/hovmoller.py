#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Plotting Hovmoller diagrams 

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


def hovmoller_anomaly(expname, startyear, endyear, refname, startref, endref, var):

    data = osi.read_averaged_hovmoller_local_anomaly_T(expname, startyear, endyear, refname, startref, endref, var)    
    delta = data[var]#/data[var].isel(time=0)-1
    pp = delta.plot(x='time', y='z', cmap=plt.cm.coolwarm)
    plt.ylim(-5000,0)

    return pp
