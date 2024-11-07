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

    refinfo = {'expname': 'lgr3', 'startyear': 2340, 'endyear': 2349}

    # global mean temperature merge from reference experiments
    #timeseries(expname='lfr0', startyear=1990, endyear=2039, varlabel='thetao', reader="post", metric="base", refinfo=None, rescale=False, avetype="standard", timeoff=0, color=None, linestyle='-', marker=None, label=None, ax=None, figname=None)
    timeseries(expname='lfr0', startyear=1990, endyear=2019, varlabel='thetao', reader='post', color='gray', linestyle='-', label='REF')

    # comparison with EOF experiments
    timeseries(expname='FE02', startyear=1990, endyear=2019, varlabel='thetao', reader='post', color='red', linestyle='-', label='EOF-TS 10y')
    timeseries(expname='FE05', startyear=1990, endyear=2019, varlabel='thetao', reader='post', color='blue', linestyle='-', label='EOF-TS 30y')

    plt.legend(
        bbox_to_anchor=(0.98, 0.98),  # x, y coordinates for legend placement
        loc='upper right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )
    plt.title('Timeseries of global mean temperature')


    # Save the combined figure
    plt.savefig(figname)

    return None


if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='thetao_FE05.png'
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
