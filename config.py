from dynaconf import Dynaconf, Validator
from pathlib import Path
import os

proj_root = Path(__file__).parent()  # /path/to/itg-cli/
config_path = proj_root.joinpath("settings.toml")

def is_writable_dir(s: str) -> bool:
    return Path(s).is_dir and os.access(s, os.W_OK)

settings = Dynaconf(
    envvar_prefix="ITG_CLI",  # export envvars with `export ITG_CLI_FOO=bar`.
    settings_files=["settings_template.toml", "settings.toml"],
    validators=[
        Validator(key, condition=lambda s: is_writable_dir)
        for key in ["PACKS", "SINGLES", "COURSES", "CACHE", "DOWNLOADS"]
    ]
    + [
        # Default to /path/to/itg-cli/.censored
        Validator(
            "CENSORED",
            default=proj_root.joinpath(".censored"),
            condition=is_writable_dir,
        ),
        Validator("DELETE_MACOS_FILES", default=False, apply_default_on_none=True),
    ],
)

# raise exception if keys are not valid
try:
    # run validators
    settings.as_dict()
except Exception as e:
    e.add_note("One or more invalid keys in settings.toml")
    e.add_note(config_path)
    raise e