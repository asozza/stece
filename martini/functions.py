
import numpy as np
import pandas as pd
import datetime
import time
from sklearn.linear_model import LinearRegression

def preproc_nemo(Tdata):
    """preprocessing routine for nemo for T grid"""

    Tdata = Tdata.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y'})
    Tdata = Tdata.rename({'deptht': 'z', 'time_counter': 'time', 'thetao': 'to'})
    Tdata = Tdata.swap_dims({'x_grid_T_inner': 'x', 'y_grid_T_inner': 'y'})
    Tdata.coords['z'] = -Tdata['z']
    
    return Tdata

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

def interp_average(xdata, ydata, N):

    x_orig = np.array(dateDecimal(xdata.values))

    for i in range(N):    
        x_filled = np.array(dateDecimal(xdata.where(xdata['time.month']==i+1,drop=True).values))
        y_filled = np.array(ydata.where(xdata['time.month']==i+1,drop=True).values.flatten())
        if (i==0):
            y_smooth = np.interp(x_orig, x_filled, y_filled)/N
        else:
            y_smooth += np.interp(x_orig, x_filled, y_filled)/N
    
    return y_smooth

def moving_average(ydata, N):

    #y_list = np.array(ydata.values.flatten())
    y_padded = np.pad(ydata, (N//2, N-1-N//2), mode='edge')
    y_smooth = np.convolve(y_padded, np.ones((N,))/N, mode='valid')

    return y_smooth

def linear_fit(Xd, Yd):
    
    model=LinearRegression()
    model.fit(Xr, Yr)    
    mp = model.coef_[0][0]
    qp = model.intercept_[0]
    
    return mp,qp

