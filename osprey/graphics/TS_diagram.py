#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics for T-S diagram

Author: Alessandro Sozza (CNR-ISAC) 
Date: Oct 2024
"""

import os
import numpy as np
import xarray as xr
import dask
import cftime
import gsw
import matplotlib.pyplot as plt

from osprey.actions.reader import reader_nemo

def TS_diagram():

    rdata = reader_nemo(expname='lgr3', startyear=2349, endyear=2349)
    rdata = rdata.isel(time=6)

    # Define the ranges for temperature and salinity
    temp_range = np.linspace(-2, 36, 100)  # Temperature in degrees Celsius
    salt_range = np.linspace(20, 40, 100)   # Salinity in PSU

    # Create meshgrid for T-S space
    T, S = np.meshgrid(temp_range, salt_range)

    # Calculate potential density for the T-S grid at a reference pressure of 0 dbar
    density_grid = gsw.sigma0(S, T)  # sigma0 is potential density anomaly with reference to 0 dbar
    # density_grid = gsw.density.rho(S, T, 0)

    # Plot 10 isolines at constant density
    density_levels = np.linspace(np.nanmin(density_grid), np.nanmax(density_grid), 10)
    contours = plt.contour(S, T, density_grid, levels=density_levels, colors='black', linestyles='--')
    plt.clabel(contours, inline=True, fmt="%.1f", fontsize=8)

    # Filter out zero values in salinity and temperature data
    salinity_data = rdata['so'].values  # Assuming salinity is in PSU
    temperature_data = rdata['thetao'].values # Assuming temperature is in °C
    mask = (salinity_data != 0) & (temperature_data != 0)
    filtered_salinity = salinity_data[mask]
    filtered_temperature = temperature_data[mask]

    # Calculate density for each filtered data point
    local_density = gsw.sigma0(filtered_salinity, filtered_temperature)
    #local_density = gsw.density.rho(filtered_salinity, filtered_temperature, 0)

    # Overlay data points colored by their local density
    sc = plt.scatter(filtered_salinity, filtered_temperature, c=local_density, cmap="plasma", edgecolor='k', s=20)
    colorbar_data = plt.colorbar(sc)
    colorbar_data.set_label("Sigma")

    # Labels and title
    plt.xlabel("Salinity (PSU)")
    plt.ylabel("Temperature (°C)")
    plt.title("T-S Diagram")
    plt.show()

