import yaml
import os

DEFAULT_VALUES = {
    'singles': '',
    'packs': '',
    'courses': '',
    'downloads': '',
    'temp_root': os.path.join(os.path.dirname(__file__), '.temp/'),
}


def load_config():
    # detect config file
    config_path = 'config.yaml'
    if os.path.exists('config.yaml') is False:
        config_path = 'config-template.yaml'
        if os.path.exists('config-template.yaml') is False:
            raise Exception('No config file found')

    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    # Validate config
    for key in DEFAULT_VALUES.keys():
        if key not in config.keys():
            config[key] = DEFAULT_VALUES[key]
        if config.get(key) is '':
            raise Exception(f'Invalid config: key "{key}" is empty or missing')
        if os.path.exists(config.get(key)) is False:
            raise Exception(
                f'Invalid config: path "{config.get(key)}" does not exist')
    return config


config_data = load_config()
