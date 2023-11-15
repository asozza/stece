#!/bin/bash

# Tool to create the ORCA2 initial conditions 

DIR=/lus/h2resw01/scratch/ccpd/orca2
adjuster=/home/ccpd/stece/epochal/orca2_adapt.py
OLD=$DIR/OLD_ORCA2
NEW=$DIR/ORCA2_ICE_v4.2.0
TGT=/lus/h2resw01/hpcperm/ccpd/ECE4-DATA/nemo
MESH=$DIR/ORCA2_mesh_mask.nc


# domain (DOES NOT WORK)
mkdir -p $TGT/domain/ORCA2
#cdo selname,glamt,glamu,glamv,glamf,gphit,gphiu,gphiv,gphif,e1t,e1u,e1v,e1f,e2t,e2u,e2v,e2f,ff_f,ff_t,e3t_1d,e3w_1d,e3t_0,e3u_0,e3v_0,e3f_0,e3w_0,e3uw_0,e3vw_0,gdept_1d,gdepw_1d,gdept_0,gdepw_0 $MESH first.nc
$adjuster $OLD/bathy_meter.nc second.nc
cdo selname,bottom_level,top_level $NEW/ORCA_R2_zps_domcfg.nc third.nc
cdo merge $MESH -chname,Bathymetry,bathy_meter second.nc third.nc $TGT/domain/ORCA2/domain_cfg.nc

rm -f first.nc second.nc third.nc


cdo selname,tmaskutil,umaskutil,vmaskutil $MESH $TGT/domain/ORCA2/maskutil.nc

#initial
mkdir -p $TGT/initial/ORCA2
for file in decay_scale_bot.nc  decay_scale_cri.nc  mixing_power_bot.nc  mixing_power_cri.nc  mixing_power_pyc.nc ; do 
    echo $file
    $adjuster $OLD/$file $TGT/initial/ORCA2/$file
done

