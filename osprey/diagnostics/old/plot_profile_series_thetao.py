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
import matplotlib.cm as cm

from osprey.graphics.profile import profile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Function to get memory usage in MB
def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 2)  # Convert bytes to megabytes (MB)


def drawing(figname):

    # Define the start and end years for the entire range
    start_year = 2040
    end_year = 2139
    step = 10  # Define the step for 10-year intervals

    # Calculate the number of profiles
    num_profiles = (end_year - start_year + 1) // step

    # Generate a color map transitioning from red to blue
    colors = ['red', 'orange', 'gold', 'green', 'darkgreen', 'deepskyblue', 'blue', 'purple', 'magenta', 'pink']

    # Create the plot
    #plt.figure(figsize=(8, 6))

    for i, start in enumerate(range(start_year, end_year + 1, step)):
        end = start + step - 1  # Define the 10-year range
        # 10-year average - last chunk
        profile(expname='FE01', startyear=start, endyear=end, varlabel='thetao', reader='post', metric='diff', replace=True, color=colors[i], linestyle='-', label=f'{start}-{end}')

    plt.legend(
        bbox_to_anchor=(0.98, 0.02),  # x, y coordinates for legend placement
        loc = 'lower right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )
    
    # Adjust layout to prevent overlap
    plt.tight_layout()

    #plt.title('Temperature profiles \n diff from REF [2390-2399]')

    # Save the combined figure
    plt.savefig(figname)

    return None


if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='fig8b.png'
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
