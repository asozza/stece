def preproc_nemo(field):
    """preprocessing routine for nemo"""

    field = field.rename_dims({'x_grid_T': 'x', 'y_grid_T': 'y', 'time_counter': 'time'})
    field = field.rename({'time_counter': 'time'})

    return field
