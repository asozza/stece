#!/bin/bash

# initiate
SECONDS=0

# read from command line
expname=$1
startyear=$2
endyear=$3
varname=$4
freqname=$5

if [[ -z $expname || -z $startyear || -z $endyear || -z $varname || -z $freqname ]] ; then
    echo " Usage: $0 expname startyear endyear varname freq [monthly or yearly] "
    exit 1
fi

# set paths
mainpath=$PERM/ece4/$expname/nemo/$varname
mkdir -p $outpath

infile=$mainpath/merged_${expname}_1y_${varname}_${startyear}-${endyear}.nc
anfile=$mainpath/anomaly_${expname}_1y_${varname}_${startyear}-${endyear}.nc

# cdo commands
cdo sub $infile -timmean $infile $anfile
cdo eof,10 $anfile.nc $mainpath/variance.nc $mainpath/pattern.nc
cdo eofcoeff $mainpath/pattern.nc $infile.nc $mainpath/timeseries

# finalize
duration=$SECONDS
echo " Elapsed Time: $((duration / 60)) minutes and $((duration % 60)) seconds "

