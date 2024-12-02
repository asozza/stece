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

from osprey.graphics.timeseries import timeseries_yearshift_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Function to get memory usage in MB
def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 2)  # Convert bytes to megabytes (MB)


def drawing(figname):

    # shift between EOF and REF experiments
    tvec, shift = timeseries_yearshift_data(expname1='FE02', startyear1=1990, endyear1=2109, expname2='lfr0', startyear2=1990, endyear2=2399, shift_threshold=500, varlabel='thetao', reader='post')

    # Definire la dimensione di un gradino (10 anni = 120 mesi)
    step_size = 121
    # Suddividere l'array in intervalli di 120 mesi e calcolare la media per ciascun gradino
    mean_values = [np.mean(shift[i:i + step_size]) for i in range(0, len(shift), step_size)]
    mean_time = [int(np.mean(tvec[i:i + step_size])) for i in range(0, len(tvec), step_size)]
    linear_curve = [mean_time[i]-1995 for i in range(0, len(mean_time))]
    delta = [mean_values[i]-linear_curve[i] for i in range(0, len(mean_values))]

    # plot
    # Create subplots: one for the curves and one for the horizontal shift
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # Plot the horizontal shift in the second subplot
    ax1.scatter(tvec, shift, color='red', s=2)
    ax1.axhline(0, color='gray', linestyle='--')  # Zero reference line
    ax1.set_xlabel('time [years]')
    ax1.set_ylabel('year shift [years]')
    ax1.legend()
    ax1.grid()

    ax2.scatter(mean_time, mean_values)
    ax2.plot(mean_time, linear_curve, color='deepskyblue', linestyle='--')
    ax2.scatter(mean_time, delta, color='green')
    ax2.set_xlabel('time [years]')
    ax2.grid()

    plt.legend(
        bbox_to_anchor=(0.98, 0.98),  # x, y coordinates for legend placement
        loc='upper right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )

    # Adjust layout to prevent overlap
    plt.tight_layout()

    #plt.title('Year shift of global mean temperature')

    # Save the combined figure
    plt.savefig(figname)

    return None


if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='fig10a.png'
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
