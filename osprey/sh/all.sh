#!/bin/bash

# initiate
SECONDS=0

# read from command line
expname=$1
startyear=$2
endyear=$3
varname=$4

if [[ -z $expname || -z $startyear || -z $endyear || -z $varname ]] ; then
    echo " Usage: ./selname.sh expname startyear endyear varname "
    exit 1
fi

# grid type
grid=T

# set paths
inipath=$SCRATCH/ece4/$expname/output/nemo
mainpath=$PERM/ece4/$expname/nemo/$varname
mkdir -p $mainpath

# filename prefix
inifix=${expname}_oce_1m_${grid}
outfix=${varname}_${freq}

# select variable and monthly average
for k in $(seq $startyear $endyear)
do
    inifile=$inipath/${inifix}_${k}-${k}.nc
    outfile=$mainpath/${outfix}_${k}-${k}.nc
	cdo yearmean -selname,$varname $inifile $outfile
done


###########################################################
# merge
# new prefix
inifix=${varname}_${freq}
outfix=merged_${varname}_${freq}

# merge cdo command
k=0
for year in $(seq $startyear $endyear); do
    inifile=$mainpath/${inifix}_${year}-${year}.nc
    echo $inifile
    if [ -f $inifile ]; then
	if [[ k -eq 0 ]]; then
	    files=$(echo $inifile)
	else
	    files=$(echo $files $inifile)
	fi
	((k++))
    else
	echo " ${inifile} not found ... "
    fi
done

outfile=$mainpath/${outfix}_${startyear}-${endyear}.nc
if [ -n "$files" ]; then
    cdo cat $files $outfile
else
    echo " Empty list! "
fi

###########################################################
# Compute EOF

# prefix
inifix=merged_${varname}
outfile=anomaly_${varname}

infile=$mainpath/merged_${varname}_${startyear}-${endyear}.nc
anfile=$mainpath/anomaly_${varname}_${startyear}-${endyear}.nc

# cdo commands
cdo sub $infile -timmean $infile $anfile
# eof or eof3d
cdo eof,10 $anfile.nc $mainpath/variance.nc $mainpath/pattern.nc
cdo eofcoeff $mainpath/pattern.nc $infile.nc $mainpath/timeseries

#############################################################
# project EOF on new field

cdo info -div $mainpath/variance.nc -timsum $mainpath/variance.nc
for k in $(seq 0 9) ; do
    const=$(cdo -s output -seltimestep,1 timeseries0000${k}.nc)
    cdo mulc,$const -seltimestep,$((k+1)) pattern.nc test${k}.nc
done
cdo -add test*.nc rebuild.nc


#################################################################
# finalize
duration=$SECONDS
echo " Elapsed Time: $((duration / 60)) minutes and $((duration % 60)) seconds "

