#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OSPREY: Ocean Spin-uP acceleratoR for Earth climatologY
--------------------------------------------------------
Osprey library for tools: bash operations and path management 

Authors
Alessandro Sozza (CNR-ISAC, 2023-2024)
"""

import os
import yaml
import subprocess
import numpy as np
import xarray as xr
import dask
import datetime
import time
import cftime
import nc_time_axis
import osprey_io as osi 

def run_bash_command(command):
    """ Run a bash command using subprocess """

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode('utf-8'))
        print(result.stderr.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with return code {e.returncode}")
        print(e.output.decode('utf-8'))
        print(e.stderr.decode('utf-8'))
        raise


def get_expname(data):
    """" Get expname from a NEMO dataset & output file path """

    return os.path.basename(data.attrs['name']).split('_')[0]


def get_nemo_timestep(filename):
    """ Get timestep from a NEMO restart file """

    return os.path.basename(filename).split('_')[1]


def epoch(date):
    """ Get epoch from date """

    s = time.mktime(date.timetuple())

    return s

def year_fraction(date):
    """ Transform date into year fraction """

    StartOfYear = datetime.datetime(date.year,1,1,0,0,0)
    EndOfYear = datetime.datetime(date.year+1,1,1,0,0,0)
    yearElapsed = epoch(date)-epoch(StartOfYear)
    yearDuration = epoch(EndOfYear)-epoch(StartOfYear)
    Frac = yearElapsed/yearDuration

    return  date.year + Frac

def count_leap_years(year1, year2):
    """ Compute number of leap years (bissextile) """
    
    leap_years = np.floor((year2 - year1 + 1) / 4) - np.floor((year2 - year1 + 1) / 100) + np.floor((year2 - year1 + 1) / 400)

    return leap_years

def count_non_leap_years(year1, year2):
    """ Compute number of non-leap years (non-bissextile) """

    total_years = year2 - year1 + 1
    leap_years = count_leap_years(year1, year2)
    non_leap_years = total_years - leap_years

    return non_leap_years

def count_total_steps(start_year, end_year, steps_per_day):
    """ Compute number of total steps in a range of years """

    leap_years = count_leap_years(start_year, end_year)
    non_leap_years = count_non_leap_years(start_year, end_year)
    total_steps = (leap_years * 366 + non_leap_years * 365) * steps_per_day

    return total_steps

def read_legfile(expname):
    """ Read date & leg from legfile """

    dirs = osi.folders(expname)
    legfile = os.path.join(dirs['exp'], 'leginfo.yml')
    with open(legfile, 'r', encoding='utf-8') as file:
        leginfo = yaml.load(file, Loader=yaml.FullLoader)
    info = leginfo['base.context']['experiment']['schedule']['leg']
    endleg = info['num']
    endyear = info['start'].year - 1

    return endleg,endyear

def get_startleg(endleg, yearspan):
    """" Get startleg from endleg and yearspan """

    return (endleg - yearspan + 1)

def get_startyear(endyear, yearspan):
    """ Get startyear from endyear and yearspan """

    return (endyear - yearspan + 1)

def get_forecast_year(year, yearleap):
    """ Get forecast year based on yearleap """

    return (year + yearleap)

def get_year(leg):
    """ Get date from leg """
    
    return (1990 + leg - 2)

def get_leg(year):
    """ Get leg from date """

    return (year - 1990 + 2)
