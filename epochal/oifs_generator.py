#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to OIFS ICs and BCs from default available ones

Authors
Paolo Davini (CNR-ISAC, Nov 2023)
"""

import subprocess
import os
from utils import extract_grid_info, ecmwf_grid

# configurable
gridname = 'TL63L91'
BASE_TGT = '/lus/h2resw01/scratch/ccpd/paleo-new'

#-----------------------#

# configurable with caution
startdate = '19900101'
ic_original_grid = 'Tco399L91' #higher resolution is better, in principle
OIFS_BASE = '/home/ccpd/hpcperm/ECE4-DATA/oifs/'

# these are only available on ATOS
OIFS_BC='/lus/h2resw01/fws1/mirror/lb/project/rdxdata/climate/climate.v015'

# these are available on atos and can be produced by oifs_create_corners.py
GRIDS = '/home/ccpd/perm/ecearth4/oifs-grids'

#-----------------------#

IC_TGT = os.path.join(BASE_TGT, gridname, startdate)
BC_TGT = os.path.join(BASE_TGT, gridname, 'climate')
os.makedirs(BC_TGT, exist_ok=True)
os.makedirs(IC_TGT, exist_ok=True)


# target grid info
grid_type, spectral, _ = extract_grid_info(gridname)
ecmwf_name = str(spectral) + ecmwf_grid(grid_type)
target_grid = 'T' + grid_type + str(spectral)

# source grid info
ic_grid_type, ic_spectral, _ = extract_grid_info(ic_original_grid)
source_grid = 'T' + ic_grid_type + str(ic_spectral)


# INITIAL CONDITIONS
print("Truncating spectral file ICMSHECE4INIT to", spectral, "harmonics")
# this is done with a clean spectral truncation with cdo
OIFS_IC = os.path.join(OIFS_BASE, ic_original_grid, startdate)
subprocess.call(["cdo", "sp2sp," + str(spectral), f"{OIFS_IC}/ICMSHECE4INIT",
                 f"{IC_TGT}/ICMSHECE4INIT"])

print ("Remapping ICMGG gaussian ICs to ", target_grid)
# this is done with remapcon using the grid fils computed with oifs_create_corner.py
#gridfile = os.path.join('grids', horizontal_grid + '.txt')
for file in ["ICMGGECE4INIT", "ICMGGECE4INIUA"]:
    print(file)
    print(["cdo", f"remapcon,{GRIDS}/{target_grid}_grid.nc", f"-setgrid,{GRIDS}/{source_grid}_grid.nc",
                     f"{OIFS_IC}/{file}", f"{IC_TGT}/{file}"])
    subprocess.call(["cdo", f"remapcon,{GRIDS}/{target_grid}_grid.nc", f"-setgrid,{GRIDS}/{source_grid}_grid.nc",
                     f"{OIFS_IC}/{file}", f"{IC_TGT}/{file}"])


# BOUNDARY CONDITIONS
print("Building BCs from ", ecmwf_name, "data")

# this is done with a mergetime of the 7 variables in the ecmwf directory based on a magic command by Klaus Wyser
variables = ["alb", "aluvp", "aluvd", "alnip", "alnid", "lail", "laih"]
paths = [f"{OIFS_BC}/{ecmwf_name}/month_{var}" for var in variables]
subprocess.call(["cdo", "-L", "mergetime"] +  paths + [f"{BC_TGT}/temp.grb"])
subprocess.call(["cdo", "settaxis,2021-01-15,00:00:00,1month", f"{BC_TGT}/temp.grb", f"{BC_TGT}/ICMCLECE4-1990"])
os.remove(f"{BC_TGT}/temp.grb")

# old method 
#var_mapping = {
#    "alb": 174,
#    "aluvp": 15,
#    "aluvd": 16,
#    "alnip": 17,
#    "alnid": 18,
#    "lail": 66,
#    "laih": 67
# #}
# ecmwf_gridname = spectral + ecmwf_name
# for var, code in var_mapping.items():
#     subprocess.call(["cdo", "-f", "grb", "--eccodes", "-setcode," + str(code),
#         "-settaxis,2021-01-15,00:00:00,1month", f"{OIFS_BC}/{ecmwf_gridname}/month_{var}", f"{BC_TGT}/{var}.grb"])
# # Merge the GRB files
# grb_files = [f"{BC_TGT}/{var}.grb" for var in var_mapping.keys()]
# subprocess.call(["cdo", "mergetime"] + grb_files + [f"{BC_TGT}/ICMCLECE4-1990"])
# # Remove the individual GRB files
# for grb_file in grb_files:
#     os.remove(grb_file)

