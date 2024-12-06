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
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))

    # Surface layer
    color='red'
    varlabel='tos'
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel=varlabel, reader='post', replace=True, avetype='moving', timeoff=0, color=color, linestyle='-', label='Surface', ax=axes[0])
    timeseries(expname='lfr1', startyear=1990, endyear=2390, varlabel=varlabel, reader='post', replace=True, avetype='moving', timeoff=410, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lfr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', replace=True, avetype='moving', timeoff=811, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lfr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', replace=True, avetype='moving', timeoff=1171, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lfr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', replace=True, avetype='moving', timeoff=1531, color=color, linestyle='-', ax=axes[0])
    #timeseries(expname='pi05', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', replace=False, avetype='moving', timeoff=1891, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lfr5', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1891, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lgr0', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2251, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lgr1', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2611, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lgr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2971, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lgr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=3331, color=color, linestyle='-', ax=axes[0])
    timeseries(expname='lgr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=3691, color=color, linestyle='-', ax=axes[0])
    axes[0].legend(loc='upper right')
    axes[0].set_xlim(1990, 6010) 
    #axes[0].set_title('Surface')

    # Pycnocline layer
    color='green'
    varlabel='thetao-pyc'
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=0, color=color, linestyle='-', label='Pycnocline', ax=axes[1])
    timeseries(expname='lfr1', startyear=1990, endyear=2390, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=410, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lfr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=811, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lfr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1171, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lfr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1531, color=color, linestyle='-', ax=axes[1])
    #timeseries(expname='pi05', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', replace=False, avetype='moving', timeoff=1891, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lfr5', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1891, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lgr0', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2251, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lgr1', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2611, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lgr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2971, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lgr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=3331, color=color, linestyle='-', ax=axes[1])
    timeseries(expname='lgr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=3691, color=color, linestyle='-', ax=axes[1])
    axes[1].legend(loc='upper right')
    axes[1].set_xlim(1990, 6010)
    #axes[1].set_title('Pycnocline')

    # Bottom layer
    color='blue'
    varlabel='sbt'
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=0, color=color, linestyle='-', label='Bottom', ax=axes[2])
    timeseries(expname='lfr1', startyear=1990, endyear=2390, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=410, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lfr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=811, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lfr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1171, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lfr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1531, color=color, linestyle='-', ax=axes[2])
    #timeseries(expname='pi05', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1891, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lfr5', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=1891, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lgr0', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2251, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lgr1', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2611, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lgr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=2971, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lgr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=3331, color=color, linestyle='-', ax=axes[2])
    timeseries(expname='lgr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', rescale=False, avetype='moving', timeoff=3691, color=color, linestyle='-', ax=axes[2])
    axes[2].legend(loc='upper right')
    axes[2].set_xlim(1990, 6010)
    #axes[2].set_title('Bottom')

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

    figname='fig0_thetao_by_layers_3.png'
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



