#!/bin/bash


target_grid=L31
start_grid=L91
horizontal_grid=TL63
INDIR=/lus/h2resw01/scratch/ccpd/paleo/${horizontal_grid}${start_grid}/19900101
OUTDIR=/lus/h2resw01/scratch/ccpd/paleo/${horizontal_grid}${target_grid}/19900101
gridfile=/home/ccpd/stece/epochal/grids/${target_grid}.txt
horfile=/home/ccpd/stece/epochal/grids/${horizontal_grid}.txt
TMPDIR=$SCRATCH/paleotest

mkdir -p $TMPDIR $OUTDIR
rm $TMPDIR/*.grb

cd $TMPDIR

# get orography and lnsp from original file
cdo selname,lnsp,z $INDIR/ICMSHECE4INIT orog.grb

# convert spectral to grid point
cdo sp2gpl $INDIR/ICMSHECE4INIT sp2gauss.grb

# convert reduced to gaussian
cdo setgridtype,regular $INDIR/ICMGGECE4INIUA gp2gauss.grb

# merge them together
cdo merge gp2gauss.grb sp2gauss.grb single.grb

# remap vertical 
cdo remapeta,$gridfile single.grb remapped.grb

# create the INITUA file
cdo --eccodes remapbil,${horfile} -selname,q,o3,crwc,cswc,clwc,ciwc,cc remapped.grb ${OUTDIR}/ICMGGECE4INIUA

# bring new field to spectral
cdo gp2spl  -selname,t,vo,d remapped.grb spback.grb

# merge and get the SH file
cdo merge orog.grb spback.grb ${OUTDIR}/ICMSHECE4INIT

# copy secondary ICM files to the output directory
cp $INDIR/ICMGGECE4INIT $OUTDIR
mkdir $OUTDIR/../climate
cp $INDIR/../climate/ICM* $OUTDIR/../climate
