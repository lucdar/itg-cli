from dynaconf import Dynaconf, Validator
from pathlib import Path
import os

proj_root = Path(__file__).parent  # /path/to/itg-cli/
config_path = proj_root.joinpath("settings.toml")


class CLISettings:
    packs: Path
    singles: Path
    courses: Path
    cache: Path
    downloads: Path
    censored: Path
    delete_macos_files: bool

    def __init__(self, settings: Dynaconf):
        self.packs = Path(settings["packs"])
        self.singles = Path(settings["singles"])
        self.courses = Path(settings["courses"])
        self.cache = Path(settings["cache"])
        self.downloads = Path(settings["downloads"])
        self.censored = Path(settings.get("censored", proj_root.joinpath(".censored")))
        self.delete_macos_files = settings.get("delete_macos_files", False)
        self.__validate()

    def __validate(self):
        dir_fields = [
            (self.packs, "packs"),
            (self.singles, "singles"),
            (self.courses, "courses"),
            (self.cache, "cache"),
            (self.downloads, "downloads"),
            (self.censored, "censored"),
        ]
        invalid_fields = []
        for d, name in dir_fields:
            if not d.is_dir and os.access(d, os.W_OK):
                invalid_fields.append((name, d))
        if len(invalid_fields) > 0:
            e = Exception("One or more invalid fields in config file:")
            for name, d in invalid_fields:
                e.add_note(f"  {name}: {str(d)}")


# TODO: define config type with Path fields
dynaconf_settings = Dynaconf(
    envvar_prefix="ITG_CLI",  # export envvars with `export ITG_CLI_FOO=bar`.
    settings_files=["settings_template.toml", "settings.toml"],
    validators=[
        Validator(key, must_exist=True)
        for key in ["PACKS", "SINGLES", "COURSES", "CACHE", "DOWNLOADS"]
    ]
    + [
        Validator("DELETE_MACOS_FILES", default=False, apply_default_on_none=True),
    ],
)

settings = CLISettings(dynaconf_settings)
