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

    refinfo = {'expname': 'lgr3', 'startyear': 2340, 'endyear': 2349, 'diagname': 'timeseries', 'format': 'global'}

    # global mean temperature merge from reference experiments
    varlabel='thetao'
    color='gray'
    timeseries(expname='lfr0', startyear=1990, endyear=2399, varlabel='thetao', reader='post', metric='diff', refinfo=refinfo, color='gray', linestyle='-', label='REF')
    timeseries(expname='lfr1', startyear=1990, endyear=2390, varlabel=varlabel, reader='post', timeoff=410, color=color, linestyle='-')
    timeseries(expname='lfr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=811, color=color, linestyle='-')
    timeseries(expname='lfr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=1171, color=color, linestyle='-')
    timeseries(expname='lfr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=1531, color=color, linestyle='-')
    timeseries(expname='lfr5', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=1891, color=color, linestyle='-')
    timeseries(expname='lgr0', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=2251, color=color, linestyle='-')
    timeseries(expname='lgr1', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=2611, color=color, linestyle='-')
    timeseries(expname='lgr2', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=2971, color=color, linestyle='-')
    timeseries(expname='lgr3', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=3331, color=color, linestyle='-')
    timeseries(expname='lgr4', startyear=1990, endyear=2349, varlabel=varlabel, reader='post', timeoff=3691, color=color, linestyle='-')

    # comparison with EOF experiments
    timeseries(expname='FE01', startyear=1990, endyear=2230, varlabel='thetao', reader='post', metric='diff', refinfo=refinfo, color='red', linestyle='-', label='EOF-T 10y')
    timeseries(expname='FE02', startyear=1990, endyear=2180, varlabel='thetao', reader='post', metric='diff', refinfo=refinfo, color='blue', linestyle='-', label='EOF-TS 10y')
    timeseries(expname='FE03', startyear=1990, endyear=2100, varlabel='thetao', reader='post', metric='diff', refinfo=refinfo, color='violet', linestyle='-', label='EOF-TS 15y')

    plt.legend(
        bbox_to_anchor=(0.98, 0.98),  # x, y coordinates for legend placement
        loc='upper right',         # Location of the legend relative to bbox_to_anchor
        borderaxespad=0           # Padding between the legend and the plot
    )
    plt.title('Timeseries of reldiff metric of global mean temperature \n wrt REF [2390-2399]')

    # Save the combined figure
    plt.savefig(figname)

    return None


if __name__ == "__main__":
    
    # Start timer
    start_time = time.time()

    figname='fig0_thetao_diff.png'
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
