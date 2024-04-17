#!/bin/bash

# Need both eccodes (grib_set) and cdo to run

target_grid=$1
start_grid=$2
horizontal_grid=$1
INDIR=/lus/h2resw01/scratch/ccpd/paleo/${horizontal_grid}${start_grid}/19900101
OUTDIR=/lus/h2resw01/scratch/ccpd/paleo/${horizontal_grid}${target_grid}/19900101
#OUTDIR=$SCRATCH/paleotest2
gridfile=/home/ccpd/stece/epochal/grids/${target_grid}.txt
horfile=/home/ccpd/stece/epochal/grids/${horizontal_grid}.txt
TMPDIR=$SCRATCH/paleotest2

mkdir -p $TMPDIR $OUTDIR
rm $TMPDIR/*.grb

cd $TMPDIR

# get orography from original file
cdo selname,z $INDIR/ICMSHECE4INIT orog.grb

# modify orography grib levels to avoid messing 
cdo selname,lnsp $INDIR/ICMSHECE4INIT lnsp.grb
vertical_levels=${target_grid:1:3}
vertical_values=$(( ($vertical_levels + 1) * 2 ))

grib_set -s numberOfVerticalCoordinateValues=${vertical_values} lnsp.grb lnsp2.grb 

# convert spectral to grid point
cdo sp2gpl -selname,vo,t,d $INDIR/ICMSHECE4INIT sp2gauss.grb

# convert reduced to gaussian
cdo setgridtype,regular $INDIR/ICMGGECE4INIUA gp2gauss.grb

# merge them together
cat gp2gauss.grb sp2gauss.grb > single.grb

# remap vertical 
cdo remapeta,$gridfile single.grb remapped.grb

# create the INITUA file
cdo --eccodes remapbil,${horfile} -selname,q,o3,crwc,cswc,clwc,ciwc,cc remapped.grb ${OUTDIR}/ICMGGECE4INIUA

# bring new field to spectral
cdo gp2spl  -selname,t,vo,d remapped.grb spback.grb

# merge and get the SH file
cat lnsp2.grb spback.grb orog.grb > ${OUTDIR}/ICMSHECE4INIT

# copy secondary ICM files to the output directory
cp $INDIR/ICMGGECE4INIT $OUTDIR
mkdir -p $OUTDIR/../climate
cp $INDIR/../climate/ICM* $OUTDIR/../climate
