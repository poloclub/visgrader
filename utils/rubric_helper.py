"""
Util to load rubric files
"""
import yaml

def get_rubric_config(config_filepath):
    with open(config_filepath, 'r') as stream:
        config = yaml.safe_load(stream)
    return config
