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

from osprey.graphics.profile import profile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Function to get memory usage in MB
def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 2)  # Convert bytes to megabytes (MB)


def drawing(figname):

    # 10-year average - last chunk
    profile(expname='lfr0', startyear=2390, endyear=2399, varlabel='so', reader='post', metric='diff', color='gray', linestyle='--', label='REF [2390-2399]')
    profile(expname='FE01', startyear=2130, endyear=2139, varlabel='so', reader='post', metric='diff', color='red', linestyle='-', label='EOF-T [2130-2139]')
    profile(expname='FE01', startyear=2080, endyear=2089, varlabel='so', reader='post', metric='diff', color='blue', linestyle='-', label='EOF-TS [2080-2089]')

    plt.legend(
        bbox_to_anchor=(0.98, 0.02),  # x, y coordinates for legend placement
        loc = 'lower right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )
    
    # Adjust layout to prevent overlap
    plt.tight_layout()

    plt.title('Salinity profiles \n diff from REF [2390-2399]')

    # Save the combined figure
    plt.savefig(figname)

    return None


if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='fig9.png'
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
