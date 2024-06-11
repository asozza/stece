"""Reader module"""

from .reader import folders,read_T,read_ice,read_domain
from .reader import preproc_nemo_domain,preproc_nemo_T,preproc_nemo_ice
from .reader import read_timeseries_T,read_profile_T,read_hovmoller_T,read_map_T,read_field_T
from .reader import read_timeseries_local_anomaly_T,read_profile_local_anomaly_T
from .reader import read_hovmoller_local_anomaly_T,read_map_local_anomaly_T
from .reader import read_averaged_timeseries_T,read_averaged_profile_T,read_averaged_hovmoller_T
from .reader import read_averaged_field_T,read_averaged_timeseries_local_anomaly_T
from .reader import read_averaged_profile_local_anomaly_T,read_averaged_hovmoller_local_anomaly_T
from .reader import read_restart,read_rebuilt,write_restart

__all__ = ["folders", 
           "read_T", "read_ice", "read_domain", "preproc_nemo_domain", "preproc_nemo_T", "preproc_nemo_ice", 
            "read_timeseries_T", "read_profile_T", "read_hovmoller_T", "read_map_T", "read_field_T", 
            "read_timeseries_local_anomaly_T", "read_profile_local_anomaly_T", 
            "read_hovmoller_local_anomaly_T", "read_map_local_anomaly_T", 
            "read_averaged_timeseries_T", "read_averaged_profile_T", "read_averaged_hovmoller_T", 
            "read_averaged_field_T", "read_averaged_timeseries_local_anomaly_T", 
            "read_averaged_profile_local_anomaly_T", "read_averaged_hovmoller_local_anomaly_T", 
            "read_restart", "read_rebuilt", "write_restart"]
