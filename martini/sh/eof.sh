#!/bin/bash

# initiate
SECONDS=0

# read from command line
expname=$1
startyear=$2
endyear=$3
varname=$4

if [[ -z $expname || -z $startyear || -z $endyear || -z $varname ]] ; then
    echo " Usage: $0 expname startyear endyear varname "
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

##################################################################################

# put together a chunk of 10 years
cdo cat alef_oce_1m_T_200* new.nc
cdo yearmean -selname,thetao new.nc pluto.nc
cdo eof3d,4 pluto.nc variance.nc pattern.nc
cdo eofcoeff pattern.nc pluto.nc timeseries.nc

cd $SCRATCH
cdo sub yearly.nc -timmean yearly.nc anom.nc
cdo eof,10 anom.nc variance.nc pattern.nc
cdo eofcoeff pattern.nc yearly.nc timeseries
cdo info -div variance.nc -timsum variance.nc
for k in $(seq 0 9) ; do
    const=$(cdo -s output -seltimestep,1 timeseries0000${k}.nc)
    cdo mulc,$const -seltimestep,$((k+1)) pattern.nc test${k}.nc
done
cdo -add test*.nc rebuild.nc
