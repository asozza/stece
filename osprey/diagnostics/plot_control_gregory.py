#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to plot graphics

Authors: Alessandro Sozza (CNR-ISAC)
Date: Sept 2024
"""

import os
import time
import psutil
import logging
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from osprey.graphics.gregory_plot import gregory_plot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Function to get memory usage in MB
def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 2)  # Convert bytes to megabytes (MB)


def drawing(figname):

    # global mean temperature merge from reference experiments
    # palette: lightcoral, red, orange, green, darkseagreen, cornflowerblue, blue, darkslategray, indigo

    gregory_plot(expname='lfr0', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lfr1', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')    
    gregory_plot(expname='lfr2', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lfr3', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lfr4', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lgr0', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lgr1', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lgr2', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lgr3', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')
    gregory_plot(expname='lgr4', startyear=1990, endyear=2399, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='gray', linestyle='--', marker='o', label='REF')

    gregory_plot(expname='FE01', startyear=1990, endyear=2240, varname1='thetao', varname2='qt_oce', reader='post', metric='base', color='red', linestyle='-', marker='o', label='EOF-T 10y')

    plt.legend(
        bbox_to_anchor=(0.98, 0.98),  # x, y coordinates for legend placement
        loc='upper right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )
    plt.title('Timeseries of global mean temperature')

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Save the combined figure
    plt.savefig(figname)

    return None


if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='fig_gregoryplot.png'
    drawing(figname)

    # End timer
    end_time = time.time()

    # Calculate total execution time
    execution_time = end_time - start_time

    # Get memory usage
    memory_usage = get_memory_usage()

    # Log execution time and memory load
    logging.info(f"Total execution time: {execution_time:.2f} seconds")
    logging.info(f"Memory load at the end: {memory_usage:.2f} MB")

