#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a command line tool to OIFS ICs and BCs from default available ones.
It can produce data from using CDO and GRIB_API. 
It uses cdo bindings for python in a rough way to allow for exploration of temporary files.


Authors
Paolo Davini (CNR-ISAC, Apr 2024)
"""

import subprocess
import os
import shutil
from utils import extract_grid_info, ecmwf_grid
import cdo
cdo = cdo.Cdo()
cdo.debug = True

# configurable
target_grid = 'TL63L31'
BASE_TGT = '/lus/h2resw01/scratch/ccpd/paleo-new'
do_clean = False

#-----------------------#

# configurable with caution
startdate = '19900101'
source_grid = 'TL159L91'
# Higher resolution is better, in principle. 
# However, differnces in original resolution might cause glitches

# where original OIFS data is found
OIFS_BASE = '/home/ccpd/hpcperm/ECE4-DATA/oifs/'

# these are only available on ATOS
OIFS_BC='/lus/h2resw01/fws1/mirror/lb/project/rdxdata/climate/climate.v015'

# these are available on atos and can be produced by oifs_create_corners.py
GRIDS = '/home/ccpd/perm/ecearth4/oifs-grids'

# temporart directory
TMPDIR = '/ec/res4/scratch/ccpd/tmpic'

#-----------------------#
IC_TGT = os.path.join(BASE_TGT, target_grid, startdate)
BC_TGT = os.path.join(BASE_TGT, target_grid, 'climate')

for d in [IC_TGT, BC_TGT, TMPDIR]:
    os.makedirs(d, exist_ok=True)

# target grid info
grid_type, spectral, vertical = extract_grid_info(target_grid)
ecmwf_name = str(spectral) + ecmwf_grid(grid_type)
target_spectral = 'T' + grid_type + str(spectral)

# source grid info
ic_grid_type, ic_spectral, ic_vertical = extract_grid_info(source_grid)
source_spectral = 'T' + ic_grid_type + str(ic_spectral)

if ic_vertical != vertical:
    print("Vertical interpolation is necessary")
    do_vertical = True
else:
    do_vertical = False


# INITIAL CONDITIONS
print("Truncating spectral file ICMSHECE4INIT to", spectral, "harmonics")
# this is done with a clean spectral truncation with cdo
OIFS_IC = os.path.join(OIFS_BASE, source_grid, startdate)
cdo.sp2sp(spectral, option="--eccodes", input=f"{OIFS_IC}/ICMSHECE4INIT", 
          output=f"{TMPDIR}/ICMSHECE4INIT")


print ("Remapping ICMGG gaussian ICs to", target_grid)
# this is done with remapcon using the grid fils computed with oifs_create_corner.py
#gridfile = os.path.join('grids', horizontal_grid + '.txt')
for file in ["ICMGGECE4INIT", "ICMGGECE4INIUA"]:
    cdo.remapcon(f"{GRIDS}/{target_spectral}_grid.nc",
                 input=f"-setgrid,{GRIDS}/{source_spectral}_grid.nc {OIFS_IC}/{file}",
                 output=f"{TMPDIR}/{file}.tmp")
    cdo.setgrid(f"grids/{target_spectral}.txt", input=f"{TMPDIR}/{file}.tmp", output=f"{TMPDIR}/{file}")
    os.remove(f"{TMPDIR}/{file}.tmp")
    
# BOUNDARY CONDITIONS
# this is done with a mergetime of the 7 variables in the ecmwf directory based on a magic command by Klaus Wyser
print("Building BCs from", ecmwf_name, "data")
variables = ["alb", "aluvp", "aluvd", "alnip", "alnid", "lail", "laih"]
paths = [f"{OIFS_BC}/{ecmwf_name}/month_{var}" for var in variables]

cdo.mergetime(options="-L", input=paths, output=f"{TMPDIR}/temp.grb")
cdo.settaxis("2021-01-15,00:00:00,1month",
             input=f"{TMPDIR}/temp.grb",
             output=f"{BC_TGT}/ICMCLECE4-1990")

os.remove(f"{TMPDIR}/temp.grb")

# move the files to the target directory
if not do_vertical:
    print("Copying files to the target directory")
    for file in ["ICMSHECE4INIT", "ICMGGECE4INIT", "ICMGGECE4INIUA"]:
        shutil.move(f"{TMPDIR}/{file}", f"{IC_TGT}/{file}")

# go for hybrid levels interpolation
else:
    print("Vertical interpolation is necessary")
    print("Select z and lnsp from ICMSHECE4INIT...")
    VERTVALUES = (int(vertical) + 1) * 2
    cdo.selname("z", input=f"{TMPDIR}/ICMSHECE4INIT", output=f"{TMPDIR}/orog.grb")
    cdo.selname("lnsp", input=f"{TMPDIR}/ICMSHECE4INIT", output=f"{TMPDIR}/lnsp.grb")
    # this is a tricky modification to avoid that CDO mess up with the final output
    subprocess.call(f"grib_set -s numberOfVerticalCoordinateValues={VERTVALUES} {TMPDIR}/lnsp.grb {TMPDIR}/lnsp2.grb", shell=True)

    # Remapeta works only on grid point space so we need to interpolate the spectral fields to gaussian
    print("Converting ICMSHECE4INIT to gaussian grid")
    cdo.sp2gpl(input=f"{TMPDIR}/ICMSHECE4INIT", output=f"{TMPDIR}/sp2gauss.grb")

    # We then bring them on the same gaussian reduced grid
    print("Remapping spectral fields from gaussian to gaussian reduced")
    cdo.remapcon(f"{GRIDS}/{target_spectral}_grid.nc", input=f"{TMPDIR}/sp2gauss.grb", output=f"{TMPDIR}/sp2gauss_reduced.grb")

    # Merge files to prepare for interpolation
    print("Merging files")
    subprocess.call(f"cat {TMPDIR}/ICMGGECE4INIUA {TMPDIR}/sp2gauss_reduced.grb > {TMPDIR}/single.grb", shell=True)

    # Hybrid levels interpolation
    print("Remapping vertical on hybrid levels")
    gridfile = f"grids/L{vertical}.txt"
    cdo.remapeta(gridfile, input=f"{TMPDIR}/single.grb", output=f"{TMPDIR}/remapped.grb")

    # create INITUA file
    print("Selecting fields to create ICMSHECE4INIUA")
    cdo.setgrid(f"grids/{target_spectral}.txt", input=f"-selname,q,o3,crwc,cswc,clwc,ciwc,cc {TMPDIR}/remapped.grb", output=f"{TMPDIR}/ICMGGECE4INIUA")

    # Nring new field to spectral space
    print("Converting back to spectral the spectral fields")
    cdo.gp2spl(input=f"-selname,t,vo,d {TMPDIR}/remapped.grb", output=f"{TMPDIR}/spback.grb")

    # Merge with orography and lnsp and get the SH file
    print("Merging files and creating the final ICMSHECE4INIT")
    subprocess.call(f"cat {TMPDIR}/lnsp2.grb {TMPDIR}/spback.grb {TMPDIR}/orog.grb > {IC_TGT}/ICMSHECE4INIT", shell=True)

    shutil.move(f"{TMPDIR}/ICMGGECE4INIT", f"{IC_TGT}/ICMGGECE4INIT")

    if do_clean:
        print("Cleaning up")
        for file in ["gp2gauss.grb", "sp2gauss.grb", "sp2gauss_reduced.grb" "single.grb", "remapped.grb", 
                    "ICMSHECE4INIT", "ICMGGECE4INIUA",
                    "remapped.grb", "spback.grb", "lnsp.grb", "lnsp2.grb", "orog.grb"]:
            os.remove(file)

if do_clean:
    os.rmdir(TMPDIR)

print("Done")
