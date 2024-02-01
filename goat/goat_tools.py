#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GOAT library for tools
(options, simple functions & miscellanea)

Authors
Alessandro Sozza (CNR-ISAC, Dec 2023)
"""

import os
import glob
import numpy as np
import xarray as xr
import pandas as pd
import datetime
import time
from sklearn.linear_model import LinearRegression

def epoch(date):

    s = time.mktime(date.timetuple())

    return s

def yearFraction(date):

    StartOfYear = datetime.datetime(date.year,1,1,0,0,0)
    EndOfYear = datetime.datetime(date.year+1,1,1,0,0,0)
    yearElapsed = epoch(date)-epoch(StartOfYear)
    yearDuration = epoch(EndOfYear)-epoch(StartOfYear)
    Frac = yearElapsed/yearDuration

    return  date.year + Frac

def dateDecimal(datatime):

    d1 = pd.to_datetime(datatime)
    x1 = [yearFraction(t) for t in d1]

    return x1
