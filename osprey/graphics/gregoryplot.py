#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Plot of gregory plots

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

