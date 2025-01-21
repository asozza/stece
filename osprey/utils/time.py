#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Time module

Author: Alessandro Sozza (CNR-ISAC) 
Date: June 2024
"""

import os
import yaml
import numpy as np
import datetime
import time

from osprey.utils.config import folders


def get_epoch(date):
    """ Get epoch from date """

    return time.mktime(date.timetuple())

def get_year_fraction(date):
    """ Transform date into year fraction """

    start_of_year = datetime.datetime(date.year,1,1,0,0,0)
    end_of_year = datetime.datetime(date.year+1,1,1,0,0,0)
    year_elapsed = get_epoch(date) - get_epoch(start_of_year)
    year_duration = get_epoch(end_of_year) - get_epoch(start_of_year)
    Frac = year_elapsed/year_duration

    return  date.year + Frac

def get_decimal_year(date):
    """ Get decimal year from year fraction """

    return [get_year_fraction(d) for d in date]

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

    dirs = folders(expname)
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

def get_year(leg, year_zero=1990):
    """ Get date from leg """
    
    return (year_zero + leg - 1)

def get_leg(year, year_zero=1990):
    """ Get leg from date """

    return (year - year_zero + 1)

def get_season_months():
    """
    Returns the list of months associated with a specified season.

    Args:
    - season (str): Name or abbreviation of the season ('winter', 'spring', 'summer', 'autumn', 
                    or 'DJF', 'MAM', 'JJA', 'SON').

    Returns:
    - list: List of months associated with the season.
    - None: If the season is invalid.
    """
    months_by_season = {
        "DJF": [12, 1, 2], 
        "MAM": [3, 4, 5], 
        "JJA": [6, 7, 8], 
        "SON": [9, 10, 11],
        "winter": [12, 1, 2],
        "spring": [3, 4, 5],
        "summer": [6, 7, 8],
        "autumn": [9, 10, 11]
    }
    
    return months_by_season
