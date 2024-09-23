from pathlib import Path
import os
from typing import Self


class CLISettings:
    user_data: Path
    singles: Path
    courses: Path
    cache: Path
    downloads: Path
    censored: Path
    delete_macos_files: bool

    def __init__(self):
        """
        Creates a new config file, attempting to populate with defaults based
        on the user's operating system. If default settings can not be inferred,
        warns the user, instructs them to populate the file manually, and exits.
        """
        raise NotImplementedError()
        # self.packs = Path(settings["packs"])
        # self.singles = Path(settings["singles"])
        # self.courses = Path(settings["courses"])
        # self.cache = Path(settings["cache"])
        # self.downloads = Path(settings["downloads"])
        # self.censored = Path(settings.get("censored", self.packs.joinpath(".censored")))
        # self.delete_macos_files = settings.get("delete_macos_files", False)
        # self.__create_missing_dirs()
        # self.__validate()

    def from_toml(path: Path) -> Self:
        """
        Returns a CLI settings object based on at path.
        Raises an exception if the fields in the config file can not be found.
        """
        raise NotImplementedError()

    def __create_missing_dirs(self):
        creatable_dir_fields = [
            (self.downloads, "downloads"),
            (self.censored, "censored"),
        ]
        for d, _ in creatable_dir_fields:
            if not d.exists():
                try:
                    d.mkdir()
                except Exception as e:
                    print(f"Failed to create missing directory {d}:", e)

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
