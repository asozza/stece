# MAIN FUNCTION
def postreader_nemo(expname, startyear, endyear, varlabel, diagname, format='plain', orca='ORCA2', replace=False, metric='base', refinfo=None):
    """ 
    Postreader_nemo: main function for reading averaged data
    
    Args:
    expname: experiment name
    startyear,endyear: time window
    varlabel: variable label (varname + ztag)
    diagname: diagnostics name [timeseries, profile, hovmoller, map, field, pdf?]
    format: time format ['plain', 'global', 'annual', 'monthly', 'seasonal']
    orca: ORCA configuration [ORCA2, eORCA1]
    replace: replace existing averaged file [False or True]
    metric: compute distance with respect to a reference field using a cost function
            all details provided in meanfield.yaml
    refinfo = {'expname': '****', 'startyear': ****, 'endyear': ****, 'mode': '*', 'format': '*'}
                with 'mode' = ['pointwise', 'meanwise']
                with 'format' = ['plain', 'global', 'annual', 'monthly', 'seasonal']

    ISSUE: forse si puo' sostituire mode con diagname? oppure fare al contrario diagname in mode?
            'pointwise' diventa 'field' etc... il problema e' che il format non si applica a tutte le diagnostiche. 
            ma solo a quelle che hanno il tempo come dimensione.
    
    """

    if '-' in varlabel:
        varname, ztag = varlabel.split('-', 1)
    else:
        varname=varlabel
        ztag=None

    dirs = folders(expname)
    info = vardict('nemo')[varname]

    ## try to read averaged data
    try:
        if not replace:
            data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric=metric)
            logger.info('Averaged data in metric "base" found.')
            return data 
    except FileNotFoundError:
        logger.info('Averaged data in metric "base" not found. Creating new file ...')

    ## otherwise read original data and perform averaging
    if metric == 'base':

        # if metric is 'base'
        ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
        data = averaging(data=ds, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
        writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric='base')
        return data

    else:

        ## if metric is not 'base', compute cost function

        if refinfo['mode'] == 'pointwise':
            
            # read reference data or create averaged field
            try:
                if not replace:
                    mds = reader_averaged(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varlabel=varlabel, diagname='field', format=refinfo['format'], metric='base')
                    logger.info('Averaged reference data in mode "pointwise" found.')
            except FileNotFoundError:
                logger.info('Averaged reference data in mode "pointwise" not found. Creating new file ...')
                xds = reader_nemo_field(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varname=varname)
                mds = averaging(data=xds, varlabel=varlabel, diagname=diagname, format=refinfo['format'], orca=orca)
                writer_averaged(data=mds, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='field', format=refinfo['format'], metric=metric)

            # apply cost function pointwisely and perform averaging afterwards
            ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
            ds = apply_cost_function(ds, mds, metric)
            data = averaging(data=ds, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
            writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname='field', format=format, metric=metric)


        elif refinfo['mode'] == 'meanwise':

            # read reference averaged data or create it
            try:
                if not replace:
                    mds = reader_averaged(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varlabel=varlabel, diagname=diagname, format=refinfo['format'], metric='base')
                    logger.info('Averaged reference data in mode "meanwise" found.')
            except FileNotFoundError:
                logger.info('Averaged reference data in mode "meanwise" not found. Creating new file ...')
                xds = reader_nemo_field(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varname=varname)
                mds = averaging(data=xds, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
                writer_averaged(data=mds, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric)

            # apply cost function according to REF format
            ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
            ds = apply_cost_function(ds, mds, metric)
            data = averaging(data=ds, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
            writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric=metric)

    # Now you can read
    data = reader_averaged(expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, metric=metric)
    
    return data






        ## if metric is not 'base', compute cost function           

        if diagname in ['timeseries', 'hovmoller', 'profile', 'field', 'map']:
            # Continua con la logica esistente, specificando quale `diagname` è compatibile con `format`
        else:
            raise ValueError(f"Unrecognized diagname: {diagname}")


        # read reference data or create averaged field
        try:
            if not replace:
                mds = reader_averaged(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], metric='base')
                logging.info('Averaged reference data found.')
        except FileNotFoundError:
            logging.info('Averaged reference data not found. Creating new file ...')
            xds = reader_nemo_field(expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varname=varname)
            mds = averaging(data=xds, varlabel=varlabel, diagname=diagname, format=refinfo['format'], orca=orca)
            writer_averaged(data=mds, expname=refinfo['expname'], startyear=refinfo['startyear'], endyear=refinfo['endyear'], varlabel=varlabel, diagname=refinfo['diagname'], format=refinfo['format'], metric=metric)

        # apply cost function and perform averaging
        ds = reader_nemo_field(expname=expname, startyear=startyear, endyear=endyear, varname=varname)
        ds = apply_cost_function(ds, mds, metric)
        data = averaging(data=ds, varlabel=varlabel, diagname=diagname, format=format, orca=orca)
        writer_averaged(data=data, expname=expname, startyear=startyear, endyear=endyear, varlabel=varlabel, diagname=diagname, format=format, metric=metric)
    





def apply_cost_function(data, mdata, metric, diagname, format):
    """
    Apply a cost function to dataset variables based on `diagname` and `format`.

    Args:
        data (xarray.Dataset): The current dataset with data variables.
        mdata (xarray.Dataset or DataArray): The reference dataset or constant values.
        metric (str): The metric used to compute the cost.
        diagname (str): The diagnostic name indicating the type of data ('field' or 'timeseries').
        format (str, optional): The format type, such as 'global' for timeseries.

    Returns:
        xarray.Dataset: A dataset containing the computed cost metrics.
    """
    # Initialize an empty dataset to store the cost results
    cost_ds = xr.Dataset(attrs={'description': f"Cost computed with metric '{metric}', diagname '{diagname}', format '{format}'"})

    if diagname == 'field':
        # Loop through each variable in the dataset and apply cost function between 4D (t,x,y,z) and 3D (x,y,z)
        for var_name in data.data_vars:
            var = data[var_name]
            
            # Check if the reference variable exists and is 3D
            if var_name in mdata.data_vars and mdata[var_name].dims == var.dims[1:]:
                var0 = mdata[var_name]
                
                # Apply cost function element-wise
                cost_result = cost(var, var0, metric)
                
                # Add result to the cost dataset
                cost_ds[var_name] = cost_result
            else:
                print(f"Skipping '{var_name}' due to dimension mismatch or missing reference variable.")

    elif diagname == 'timeseries' and format == 'global':
        # Loop through each variable in the dataset and apply cost function between timeseries (t) and constant
        for var_name in data.data_vars:
            var = data[var_name]
            
            # Check if mdata has a single constant value
            if var_name in mdata.data_vars and mdata[var_name].size == 1:
                var0 = mdata[var_name]
                
                # Apply cost function across the time dimension
                cost_result = cost(var, var0, metric)
                
                # Add result to the cost dataset
                cost_ds[var_name] = cost_result
            else:
                print(f"Skipping '{var_name}' due to missing constant reference.")

    else:
        raise ValueError(f"Unrecognized diagname '{diagname}' or format '{format}' for this function.")

    return cost_ds