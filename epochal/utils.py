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

def extract_grid_info(string):
    """Extract grid info from a string"""
    pattern = r'T(co|L)(\d+)L(\d+)'
    match = re.match(pattern, string)
    if match:
        grid_type = match.group(1)
        spectral = int(match.group(2))
        num_levels = int(match.group(3))
        return grid_type, spectral, num_levels
    else:
        return None
    
def spectral2gaussian(spectral, kind):
    """Convert spectral resolution to gaussian"""
    if kind == "co":
        return int(spectral) + 1
    if kind == "L":
        return int((int(spectral) + 1) / 2)

    raise ValueError("Unknown grid type")   
