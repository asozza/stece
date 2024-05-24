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
    echo " Usage: ./merge.sh expname startyear endyear varname freq [monthly, yearly] "
    exit 1
fi

if [[ $freqname != 'monthly' && $freqname != 'yearly' ]] ; then
    echo " Unknown frequency. Available options: [monthly, yearly] "
    exit 1
fi

# set flag for frequency
if [ $freqname == 'monthly' ]; then    
    freq=1m
fi
if [ $freqname == 'yearly' ]; then    
    freq=1y
fi

# set paths
mainpath=$PERM/ece4/$expname/nemo/$varname
mkdir -p $mainpath

# prefix
inifix=${varname}_${freq}
outfix=merged_${varname}_${freq}

# cdo commands
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

# finalize
duration=$SECONDS
echo " Elapsed Time: $((duration / 60)) minutes and $((duration % 60)) seconds "

