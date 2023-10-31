#!/bin/bash

gridname=TL159L91
OIFS_BC=/lus/h2resw01/fws1/mirror/lb/project/rdxdata/climate/climate.v015
OIFS_IC=/home/ccpd/hpcperm/ECE4-DATA/oifs/
IC_TGT=/lus/h2resw01/scratch/ccpd/paleo/$gridname/19900101
BC_TGT=/lus/h2resw01/scratch/ccpd/paleo/$gridname/climate
mkdir -p ${BC_TGT} ${IC_TGT}

#target_grid='159l_2'
target_grid='159l_2'
ic_original_grid='TL159L91'
spectral_truncation=$(echo ${target_grid} | cut -f1 -d'l')

# ic
echo "ICMSHECE4INIT"
cdo sp2sp,${spectral_truncation} ${OIFS_IC}/${ic_original_grid}/19900101/ICMSHECE4INIT ${IC_TGT}/ICMSHECE4INIT
for file in ICMGGECE4INIT ICMGGECE4INIUA ; do
    echo $file
    cdo remapnn,${OIFS_BC}/${target_grid}/10_bats_glcc.grb ${OIFS_IC}/${ic_original_grid}/19900101/$file ${IC_TGT}/$file
done

# bc
for var in alb aluvp aluvd alnip alnid lail laih ; do
    case $var in 
        alb) code=174 ;;
        aluvp) code=15 ;; 
        aluvd) code=16 ;;
        alnip) code=17 ;;
        alnid) code=18 ;;
        lail) code=66 ;; 
        laih) code=67 ;;

    esac
    cdo -f grb --eccodes -setcode,$code -settaxis,2021-01-15,00:00:00,1month ${OIFS_BC}/${target_grid}/month_${var} ${BC_TGT}/${var}.grb
done
rm -f ${BC_TGT}/ICMCLECE4-1990
cdo mergetime ${BC_TGT}/*.grb ${BC_TGT}/ICMCLECE4-1990
rm ${BC_TGT}/*.grb
