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

from osprey.graphics.timeseries import timeseries

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Function to get memory usage in MB
def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 2)  # Convert bytes to megabytes (MB)


def drawing(figname):

    # global mean temperature merge from reference experiments
    # palette: lightcoral, red, orange, green, darkseagreen, cornflowerblue, blue, darkslategray, indigo
    color='blue'
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='thetao', reader='post', timeoff=0, color=color, linestyle='-', label='lfr0')
    timeseries(expname='lfr1', startyear=1990, endyear=2390, varlabel='thetao', reader='post', timeoff=410, color=color, linestyle='-', label='lfr1')
    timeseries(expname='lfr2', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=811, color=color, linestyle='-', label='lfr2')
    timeseries(expname='lfr3', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=1171, color=color, linestyle='-', label='lfr3')
    timeseries(expname='lfr4', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=1531, color=color, linestyle='-', label='lfr4')
    timeseries(expname='lfr5', startyear=1990, endyear=2349, varlabel='thetao', reader='post', timeoff=1891, color=color, linestyle='-', label='lfr5')
    timeseries(expname='lgr0', startyear=1990, endyear=2220, varlabel='thetao', reader='post', timeoff=2251, color=color, linestyle='-', label='lgr0')

    # comparison with EOF experiments
    #timeseries(expname='FE01', startyear=1990, endyear=2139, varlabel='thetao', reader='post', timeoff=0, color='red', linestyle='-', label='EOF-T')
    #timeseries(expname='FE02', startyear=1990, endyear=2089, varlabel='thetao', reader='post', timeoff=0, color='blue', linestyle='-', label='EOF-TS')

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

    figname='fig3a.png'
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
