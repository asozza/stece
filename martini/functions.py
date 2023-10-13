import datetime
import time
import numpy as np

def preproc_nemo(field):
    """preprocessing routine for nemo"""

    field = field.rename_dims({'deptht': 'z','x_grid_T': 'x', 'y_grid_T': 'y', 'time_counter': 'time'})
    field = field.rename({'deptht': 'z','time_counter': 'time'})

    return field

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
    return field
