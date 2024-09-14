from dynaconf import Dynaconf, Validator
import os

PROJ_ROOT = os.path.dirname(__file__)  # /path/to/itg-cli/
CONFIG_PATH = os.path.join(PROJ_ROOT, "settings.toml")

def is_writable_dir(s: str) -> bool:
    return os.path.isdir(s) and os.access(s, os.W_OK)

settings = Dynaconf(
    envvar_prefix="ITG_CLI",  # export envvars with `export ITG_CLI_FOO=bar`.
    settings_files=["settings.toml"],
    validators=[
        Validator(key, condition=lambda s: is_writable_dir)
        for key in ["PACKS", "SINGLES", "COURSES", "CACHE", "DOWNLOADS"]
    ]
    + [
        # Default to /path/to/itg-cli/.censored
        Validator(
            "CENSORED",
            default=os.path.join(PROJ_ROOT, ".censored"),
            condition=is_writable_dir,
        ),
        Validator(
            "TEMP",
            default=os.path.join(PROJ_ROOT, ".temp"),
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
    e.add_note(CONFIG_PATH)
    raise e