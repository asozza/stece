#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dictionary of coordinates

Author: Alessandro Sozza (CNR-ISAC)
Date: Nov 2024
"""


def coordict(use_cft):
    """ Dictionary of coordinates in EC-Earth """

    coordlist = {
        
        "time": {"axis": "T", 
                 "standard_name": "time",
                 "long_name": "time",
                 "calendar": "gregorian",
                 "units": "seconds",
                 "time_origin": "1990-01-01 00:00:00"},
        "lat": {"standard_name": "latitude",
                "long_name": "latitude",
                "units": "degrees"},
        "lon": {"standard_name": "longitude",
                "long_name": "longitude",
                "units": "degrees"},
        "month": {"standard_name": "month",
                 "long_name": "month",                 
                 "units": "months"},
        "season": {"standard_name": "season",
                 "long_name": "season",                 
                 "units": "seasons"},
        "year": {"standard_name": "year",
                 "long_name": "year",                 
                 "units": "years"}

    }

