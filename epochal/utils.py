"""Some utilities for OIFS grid definition"""

import re

def get_info_grid(gridname):

    """Get the info on the grid to find the right ECMWF file"""

    kind = re.sub("[0-9]", "", gridname)[1:].upper()
    spectral = re.sub("[^0-9]", "", gridname)
    ecmwf_name = {
        'L': 'l_2',
        'CO': '_4',
        'Q': '_2'
    }

    return spectral, ecmwf_name[kind]
