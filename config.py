import yaml
import os

PROJ_ROOT = os.path.dirname(__file__)  # path to .../itg-cli/

# Default values for config if the corresponding keys aren't found in config.yaml
DEFAULT_VALUES = {
    "singles": "",
    "packs": "",
    "courses": "",
    "cache": "",
    "downloads": "",
    "temp_root": os.path.join(PROJ_ROOT, ".temp/"),
    "censored": os.path.join(PROJ_ROOT, ".censored/"),
    "delete-macos-files": False,
}


def load_config():
    # detect config file
    config_path = os.path.join(PROJ_ROOT, "config.yaml")
    if os.path.exists(config_path) is False:
        config_path = os.path.join(PROJ_ROOT, "config-template.yaml")
        if os.path.exists(config_path) is False:
            raise Exception("No config file found")

    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    # Validate config
    for key in DEFAULT_VALUES.keys():
        if key not in config.keys():
            config[key] = DEFAULT_VALUES[key]
        if config.get(key) == "":
            raise Exception(f'Invalid config: key "{key}" is empty or missing')
        if os.path.exists(config.get(key)) is False:
            if key in ["temp_root", "censored"]:
                os.makedirs(config.get(key))
            else:
                raise Exception(
                    f'Invalid config: path "{config.get(key)}" does not exist'
                )
    return config


config_data = load_config()
