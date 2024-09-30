#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to plot graphics

Authors: Alessandro Sozza (CNR-ISAC)
Date: Sept 2024
"""

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import logging

from osprey.graphics.timeseries import timeseries

def drawing(figname):

    # Create a figure with 3 subplots (one for each layer)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Surface layer
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='tos', reader='post', 
               rescale=False, color='lightcoral', linestyle='--', label='surface - REF', ax=axes[0])
    timeseries(expname='FE01', startyear=1990, endyear=2139, varlabel='tos', reader='post', 
               rescale=False, color='red', linestyle='-', label='surface - EOF', ax=axes[0])
    axes[0].legend(loc='upper right')
    axes[0].set_title('Surface Layer')

    # Pycnocline layer
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='thetao-pyc', reader='post', 
               rescale=False, color='darkseagreen', linestyle='--', label='pycnocline - REF', ax=axes[1])
    timeseries(expname='FE01', startyear=1990, endyear=2139, varlabel='thetao-pyc', reader='post', 
               rescale=False, color='green', linestyle='-', label='pycnocline - EOF', ax=axes[1])
    axes[1].legend(loc='upper right')
    axes[1].set_title('Pycnocline Layer')

    # Bottom layer
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='sbt', reader='post', 
        rescale=False, color='cornflowerblue', linestyle='--', label='bottom - REF', ax=axes[2])
    timeseries(expname='FE01', startyear=1990, endyear=2139, varlabel='sbt', reader='post', 
        rescale=False, color='blue', linestyle='-', label='bottom - EOF', ax=axes[2])
    axes[2].legend(loc='upper right')
    axes[2].set_ylabel('Temperature [degC]')
    axes[2].set_xlabel('Time [years]')

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Set the main title for the figure
    fig.suptitle('Temperature by Ocean Layer', fontsize=16, y=1.02)

    # Save the combined figure
    plt.savefig(figname)

    return fig

if __name__ == "__main__":
    
    figname='fig3.png'
    drawing(figname)


