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

from osprey.graphics.gregory_plot import gregory_plot

def drawing(figname):

    gregory_plot(expname='lfr0', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='nemo', metric='base', color='lightcoral', linestyle='--', label='REF')
    gregory_plot(expname='FE01', startyear=1990, endyear=2139, varname1='thetao', varname2='qt_oce', reader='nemo', metric='base', color='red', linestyle='-', label='EOF')
    plt.legend(
        bbox_to_anchor=(0.98, 0.98),  # x, y coordinates for legend placement
        loc='upper right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )
    plt.title('Gregory plot')

    # Save the combined figure
    plt.savefig(figname)

    return None

if __name__ == "__main__":
    
    figname='fig4.png'
    drawing(figname)


