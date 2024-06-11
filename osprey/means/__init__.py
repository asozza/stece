"""Means module"""

from .means import flatten_to_triad, elements, subrange, movave, cumave 
from .means import timemean, globalmean, spacemean
from .means import cost, mean_forecast_error

from .eof import preproc_timeseries_3D,preproc_pattern_3D
from .eof import preproc_variance,preproc_forecast_3D
from .eof import cdo_merge,cdo_selname,cdo_detrend,cdo_EOF
from .eof import cdo_retrend,cdo_info_EOF
from .eof import create_EOF,save_EOF


__all__ = ["flatten_to_triad", "elements", "subrange", "movave", "cumave",
           "timemean", "globalmean", "spacemean", 
           "cost", "mean_forecast_error",
           "preproc_timeseries_3D", "preproc_pattern_3D",
           "preproc_variance","preproc_forecast_3D",
           "cdo_merge","cdo_selname","cdo_detrend","cdo_EOF",
           "cdo_retrend","cdo_info_EOF","create_EOF","save_EOF"]
