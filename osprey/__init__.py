"""OSPREY module"""

from .actions import rebuilder,rollbacker,replacer
from .actions import forecaster_fit, forecaster_EOF, stabilizer

from .graphics import timeseries,timeseries_diff,timeseries_anomaly
from .graphics import profile,profile_diff
from .graphics import gregoryplot
from .graphics import hovmoller,hovmoller_anomaly

from .means import flatten_to_triad, elements, subrange, movave, cumave 
from .means import timemean, globalmean, spacemean
from .means import cost, mean_forecast_error

from .means import preproc_timeseries_3D,preproc_pattern_3D
from .means import preproc_variance,preproc_forecast_3D
from .means import cdo_merge,cdo_selname,cdo_detrend,cdo_EOF
from .means import cdo_retrend,cdo_info_EOF
from .means import create_EOF,save_EOF

from .utils import run_bash_command, get_expname, get_nemo_timestep
from .utils import epoch, year_fraction, count_leap_years, count_non_leap_years
from .utils import count_total_steps, read_legfile, get_startleg, get_startyear
from .utils import get_forecast_year, get_year, get_leg, dateDecimal

__all__ = ["rebuilder", "rollbacker", "replacer", "forecaster_fit", "forecaster_EOF", "stabilizer",
           "run_bash_command", "get_expname", "get_nemo_timestep", "epoch", "year_fraction", 
           "count_leap_years", "count_non_leap_years", "count_total_steps", "dateDecimal", 
           "read_legfile", "get_startleg", "get_startyear", "get_forecast_year", "get_year", "get_leg"]
