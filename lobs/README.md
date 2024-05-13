
```
    _       _         _
   | |     | |  ___ _| |_  ___  _
   | | ___ | |_/ __|_   _|/ _ \| |__
   | |/ _ \| _ \__ \ | |_|  __/|  _/        
   |_|\___/|___/___/ |____\___\|_|          
_______________________________________
LOad Balancing ScripT for Ec-earth fouR
```

## Overview

"Load Balancing Script for ec-earth4" (LOBSTER) is a suite for evaluation of simulation performance of EC-Earth4.

## Documentation

files needed:

- [ ]  `NODE.001_01`
- [ ]  `leginfo.yml`
- [ ]  `timing.log`
- [ ]  `paths.yml` (optional)

## Examples

see jupiter notebook test.ipynb

loaded libraries:

``` 
import numpy as np
import matplotlib.pyplot as plt
import lobster as lobs
```

available commands:

- [x] single plot: `lobs.plot_sypd_vs_time(expname, leg)`
- [x] multi plots:  `lobs.multiplot_vs_time(expname, leg)`
- [x] multi experiments: `lobs.plot_sypd_vs_nptot([exp1,exp2,...], leg)`
- [x] save table: `lobs.save_table(expnames, leg)`