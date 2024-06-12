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
    echo " Usage: ./selname.sh expname startyear endyear varname freq [monthly or yearly] "
    exit 1
fi

if [[ $freqname != 'monthly' && $freqname != 'yearly' ]] ; then
    echo " Unknown frequency. Available options: monthly, yearly " 
    exit 1
fi

# set flag for frequency
if [ $freqname == 'monthly' ]; then    
    freq=1m
fi
if [ $freqname == 'yearly' ]; then    
    freq=1y
fi

# grid type
grid=T

# set paths
inipath=$SCRATCH/ece4/$expname/output/nemo
outpath=$PERM/ece4/$expname/nemo/$varname
mkdir -p $outpath

# filename prefix
inifix=${expname}_oce_1m_${grid}
outfix=${varname}_${freq}

# cdo commands
for k in $(seq $startyear $endyear)
do
    inifile=$inipath/${inifix}_${k}-${k}.nc
    outfile=$outpath/${outfix}_${k}-${k}.nc
    # monthly frequency 
    if [ $freqname == 'monthly' ]; then
	cdo -selname,$varname $inifile $outfile
    fi
    # yearly frequency
    if [ $freqname == 'yearly' ]; then
	cdo yearmean -selname,$varname $inifile $outfile
    fi
done

# finalize
duration=$SECONDS
echo " Elapsed Time: $((duration / 60)) minutes and $((duration % 60)) seconds "

