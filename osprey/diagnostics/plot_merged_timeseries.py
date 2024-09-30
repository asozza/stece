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

    # global mean temperature merge from reference experiments
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='thetao', reader='post', timeoff=0, color='lightcoral', linestyle='-', label='lfr0')
    timeseries(expname='lfr1', startyear=1990, endyear=2390, varlabel='thetao', reader='post', timeoff=410, color='red', linestyle='-', label='lfr1')
    timeseries(expname='lfr2', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=811, color='orange', linestyle='-', label='lfr2')
    timeseries(expname='lfr3', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=1171, color='green', linestyle='-', label='lfr3')
    timeseries(expname='lfr4', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=1531, color='darkseagreen', linestyle='-', label='lfr4')
    timeseries(expname='lfr5', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=1891, color='cornflowerblue', linestyle='-', label='lfr5')
    timeseries(expname='lfr6', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=2251, color='blue', linestyle='-', label='lfr6')

    plt.legend(
        bbox_to_anchor=(0.98, 0.98),  # x, y coordinates for legend placement
        loc='upper right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )
    plt.title('Timeseries of global mean temperature \n from the reference experiments')


    # Save the combined figure
    plt.savefig(figname)

    return None

if __name__ == "__main__":
    
    figname='fig4.png'
    drawing(figname)


