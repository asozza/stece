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
    varlabel='thetao'
    #timeseries(expname='pi00', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=0, color='blue', linestyle='-')
    #timeseries(expname='pi01', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=360, color='blue', linestyle='-')
    #timeseries(expname='pi02', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=720, color='blue', linestyle='-')
    #timeseries(expname='pi03', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=1080, color='blue', linestyle='-')
    #timeseries(expname='pi04', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=1440, color='blue', linestyle='-')
    #timeseries(expname='pi05', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=1800, color='blue', linestyle='-')
    #timeseries(expname='pi06', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=2160, color='blue', linestyle='-')
    #timeseries(expname='pi07', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=2520, color='blue', linestyle='-')
    timeseries(expname='pi08', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=2880, color='blue', linestyle='-')
    #timeseries(expname='pi09', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=3240, color='blue', linestyle='-')
    
    plt.title('Timeseries of global mean temperature')

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Save the combined figure
    plt.savefig(figname)

    return None


if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='pi00-01_thetao.png'
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

