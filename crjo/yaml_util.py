"""
Module to load and manipulate yaml file with ruamel package

Authors
Matteo Nurisso (CNR-ISAC, Mar 2024)
"""
import os
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq

def load_yaml(file: str= None, ruamel_type: str = 'rt'):
    """
    Load yaml file with ruamel.yaml package

    Args:
        file (str): a file path to the yaml
        ruamel_type (str, optional): the type of YAML initialisation.
                                     Default is 'rt' (round-trip)

    Returns:
        A dictionary with the yaml file keys
    """

    if not os.path.exists(file):
        raise ValueError(f'File {file} not found: you need to have this configuration file!')

    yaml = YAML(typ=ruamel_type)

    # Load the YAML file as a text string
    with open(file, 'r', encoding='utf-8') as file:
        yaml_text = file.read()
    
    cfg = yaml.load(yaml_text)

    if isinstance(cfg, CommentedSeq):
        cfg = cfg[0]

    return cfg

def modify_rundir(run_dir: str = None, path: str = None):
    """
    Modify the run_dir in the yaml file
    """

    if path is None:
        raise ValueError('path is None')

    # Open yaml file
    file = load_yaml(path)

    # Modify rundir
    try:
        old_value = file['base.context']['experiment']['run_dir']
        # print(f'Old value: {old_value}') # Debug purpose

        # modify old_value.value keeping the TaggedScalar
        file['base.context']['experiment']['run_dir'].value = run_dir
    except KeyError:
        raise KeyError('Key not found')
    
    return file


def save_yaml(path: str = None, cfg: dict = None, ruamel_type: str = 'rt'):
    """
    Save dictionary to a yaml file with ruamel.yaml package

    Args:
        path (str): a file path to the yaml
        cfg (dict): a dictionary to be dumped
        ruamel_type (str, optional): the type of YAML initialisation.
                                    Default is 'rt' (round-trip)
    """
    # Initialize YAML object
    yaml = YAML(typ=ruamel_type)

    # Check input
    if path is None:
        raise ValueError('File not defined')
    if cfg is None:
        raise ValueError('Content cfg not defined')

    # Dump to file
    with open(path, 'w', encoding='utf-8') as path:
        yaml.dump(cfg, path)

    return None