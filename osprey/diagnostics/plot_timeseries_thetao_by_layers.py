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


# MAIN FUNCTION
def drawing(figname):

    # Create a figure with 3 subplots (one for each layer)
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))

    # Surface layer
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='tos', reader='post', rescale=False, color='lightcoral', linestyle='--', label='surface - REF', ax=axes[0])
    timeseries(expname='FE01', startyear=1990, endyear=2139, varlabel='tos', reader='post', rescale=False, color='red', linestyle='-', label='surface - EOF-T', ax=axes[0])
    timeseries(expname='FE02', startyear=1990, endyear=2089, varlabel='tos', reader='post', rescale=False, color='orange', linestyle='-', label='surface - EOF-TS', ax=axes[0])
    axes[0].legend(loc='upper right')
    axes[0].set_title('Surface')

    # Pycnocline layer
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='thetao-pyc', reader='post', rescale=False, color='darkseagreen', linestyle='--', label='pycnocline - REF', ax=axes[1])
    timeseries(expname='FE01', startyear=1990, endyear=2139, varlabel='thetao-pyc', reader='post', rescale=False, color='green', linestyle='-', label='pycnocline - EOF-T', ax=axes[1])
    timeseries(expname='FE02', startyear=1990, endyear=2089, varlabel='thetao-pyc', reader='post', rescale=False, color='lime', linestyle='-', label='pycnocline - EOF-TS', ax=axes[1])
    axes[1].legend(loc='upper right')
    axes[1].set_title('Pycnocline')

    # Bottom layer
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='sbt', reader='post', rescale=False, color='cornflowerblue', linestyle='--', label='bottom - REF', ax=axes[2])
    timeseries(expname='FE01', startyear=1990, endyear=2139, varlabel='sbt', reader='post', rescale=False, color='blue', linestyle='-', label='bottom - EOF-T', ax=axes[2])
    timeseries(expname='FE02', startyear=1990, endyear=2089, varlabel='sbt', reader='post', rescale=False, color='deepskyblue', linestyle='-', label='bottom - EOF-TS', ax=axes[2])
    axes[2].legend(loc='upper left')
    axes[2].set_title('Bottom')

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Set the main title for the figure
    #fig.suptitle('Temperature by ocean layer')

    # Save the combined figure
    plt.savefig(figname)

    return fig

if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='fig5.png'
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



