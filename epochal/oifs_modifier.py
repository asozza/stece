#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tool to modify OIFS ICs/BCs"""
# INITIAL CONDITIONS
import subprocess
import os
import xarray as xr


INDIR='/lus/h2resw01/hpcperm/ccpd/ECE4-DATA/oifs/TL63L31/19900101'
OUTDIR='/lus/h2resw01/scratch/ccpd/OIFS-playground'


OIFS_SPECTRAL = "ICMSHECE4INIT"
print("ICMSHECE4INIT")
subprocess.call(["cdo", "-f", "nc4", "sp2gpl", f"{INDIR}/{OIFS_SPECTRAL}",
                 f"{OUTDIR}/grid_point.nc"])

sh = xr.open_dataset(f"{OUTDIR}/grid_point.nc")
print(sh)
sh['z'] = sh['z'] * 0
sh.to_netcdf(f"{OUTDIR}/grid_point_new.nc")

subprocess.call(["cdo", "-f", "grb2", "gp2spl", f"{OUTDIR}/grid_point_new.nc",
                 f"{OUTDIR}/{OIFS_SPECTRAL}"])

OIFS_INIT = "ICMGGECE4INIT"
subprocess.call(["cdo", "--eccodes", "-f", "nc4", "copy", f"{INDIR}/{OIFS_INIT}",
                  f"{OUTDIR}/init.nc"])
init = xr.open_dataset(f"{OUTDIR}/init.nc")
print(init)
init['al'] = init['al'] + 0.05
init.to_netcdf(f"{OUTDIR}/init_new.nc")

subprocess.call(["cdo", "--eccodes", "-f", "grb", f"-setgrid,{INDIR}/{OIFS_INIT}", f"{OUTDIR}/init_new.nc",
                 f"{OUTDIR}/{OIFS_INIT}"])


subprocess.call(["cp", f"{INDIR}/ICMGGECE4INIUA", f"{OUTDIR}/ICMGGECE4INIUA"])

for file in os.listdir(OUTDIR):
    if file.endswith(".nc") or file.endswith(".grb"):
        os.remove(os.path.join(OUTDIR, file))
