#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to OIFS ICs and BCs from default available ones

Authors
Paolo Davini (CNR-ISAC, Nov 2023)
"""

import subprocess
import os
from utils import get_info_grid

# configurable
gridname = 'TL63L91'
BASE_TGT = '/lus/h2resw01/scratch/ccpd/paleo-new'

#-----------------------#

# configurable with caution
startdate = '19900101'
ic_original_grid = 'TL159L91'
OIFS_BASE = '/home/ccpd/hpcperm/ECE4-DATA/oifs/'

# these are only available on ATOS
OIFS_BC='/lus/h2resw01/fws1/mirror/lb/project/rdxdata/climate/climate.v015'

#-----------------------#

IC_TGT = os.path.join(BASE_TGT, gridname, startdate)
BC_TGT = os.path.join(BASE_TGT, gridname, 'climate')
os.makedirs(BC_TGT, exist_ok=True)
os.makedirs(IC_TGT, exist_ok=True)

horizontal_grid = gridname[:-3]
spectral, ecmwf_name = get_info_grid(horizontal_grid)


# INITIAL CONDITIONS
OIFS_IC = os.path.join(OIFS_BASE, ic_original_grid, startdate)
print("ICMSHECE4INIT")
subprocess.call(["cdo", "sp2sp," + spectral, f"{OIFS_IC}/ICMSHECE4INIT", f"{IC_TGT}/ICMSHECE4INIT"])

gridfile = os.path.join('grids', horizontal_grid + '.txt')
for file in ["ICMGGECE4INIT", "ICMGGECE4INIUA"]:
    print(file)
    subprocess.call(["cdo", f"remapnn,{gridfile}", f"{OIFS_IC}/{file}", f"{IC_TGT}/{file}"])

# BOUNDARY CONDITIONS
var_mapping = {
    "alb": 174,
    "aluvp": 15,
    "aluvd": 16,
    "alnip": 17,
    "alnid": 18,
    "lail": 66,
    "laih": 67
}

ecmwf_gridname = spectral + ecmwf_name
for var, code in var_mapping.items():
    subprocess.call(["cdo", "-f", "grb", "--eccodes", "-setcode," + str(code),
        "-settaxis,2021-01-15,00:00:00,1month", f"{OIFS_BC}/{ecmwf_gridname}/month_{var}", f"{BC_TGT}/{var}.grb"])

# Merge the GRB files
grb_files = [f"{BC_TGT}/{var}.grb" for var in var_mapping.keys()]
subprocess.call(["cdo", "mergetime"] + grb_files + [f"{BC_TGT}/ICMCLECE4-1990"])

# Remove the individual GRB files
for grb_file in grb_files:
    os.remove(grb_file)
