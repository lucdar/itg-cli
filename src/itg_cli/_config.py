import os
import platform
import tomlkit
from importlib.resources import files
from tomlkit.toml_file import TOMLFile
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "itg-cli.toml"
TEMPLATE_PATH = files("itg_cli").joinpath("config_template.toml")


class CLISettings:
    location: Path  # The path to the .toml file
    root: Path
    singles: Path
    delete_macos_files: bool
    downloads: Path | None
    packs: Path
    courses: Path
    cache: Path

    def __init__(self, toml: Path):
        """
        Creates a CLI settings object based on the toml file at `toml`.

        If `toml` does not exist, creates a new .toml file with defaults based
        on the user's operating system. If default settings can not be inferred,
        warns the user, instructs them to populate the file manually, and exits.
        """
        self.location = toml
        if not self.location.exists():
            self.__write_default_toml(toml)

        # Ensure required tables are present
        toml_doc = TOMLFile(toml).read()
        for table in ["required", "optional"]:
            if table not in toml_doc:
                e = Exception(f"Missing table ({table}) in config:")
                e.add_note(f"{self.location}")
                raise e
        # Ensure required fields are set
        required = toml_doc["required"]
        for key in ["root", "singles_pack_name", "delete_macos_files"]:
            value = required.get(key)
            if value is None or value == "":
                e = Exception(
                    f"Required config value ({value}) is empty or unbound in config:"
                )
                e.add_note(f"{self.location}")
                raise e

        # Set properties
        self.root = Path(required["root"])
        self.delete_macos_files = bool(required["delete_macos_files"])
        # Infer unbound or empty string bindings for optional keys
        optional = toml_doc["optional"]
        downloads = optional.get("downloads")
        self.downloads = None if not downloads else Path(downloads)
        self.packs = Path(optional.get("packs") or self.root / "Songs")
        self.courses = Path(optional.get("courses") or self.root / "Courses")
        self.cache = Path(optional.get("cache") or self.root / "Cache")
        self.singles = self.packs / required["singles_pack_name"]

        self.__validate_dirs()

    def __write_default_toml(self, toml: Path):
        """
        Writes a itg-cli config file to `toml` with platform-specific defaults set.
        """
        template = TOMLFile(TEMPLATE_PATH).read()
        match platform.system():
            case "Windows":
                root = Path(os.getenv("APPDATA")) / "ITGmania"
            case "Linux":
                # TODO: verify/add new locations
                root = Path.home() / ".itgmania"
            case "Darwin":  # MacOS
                root = Path.home() / "Library" / "Application Support" / "ITGmania"
                cache = Path.home() / "Library" / "Caches" / "ITGmania"
                template["optional"]["cache"] = tomlkit.string(str(cache), literal=True)
            case _:
                raise Exception("Unsupported platform.")
        template["required"]["root"] = tomlkit.string(str(root), literal=True)
        toml.parent.mkdir(parents=True, exist_ok=True)
        TOMLFile(toml).write(template)
        print(f"Created new config file at {toml}")

    def __validate_dirs(self):
        dir_fields = [
            (self.packs, "packs"),
            (self.singles, "singles"),
            (self.courses, "courses"),
            (self.cache, "cache"),
            (self.downloads, "downloads"),
        ]
        invalid_fields = []
        for d, name in dir_fields:
            if name == "singles" and d.parent.exists():
                d.mkdir(exist_ok=True)
            if name == "downloads" and d is None:
                continue
            if not d.is_dir and os.access(d, os.W_OK):
                invalid_fields.append((name, d))
        if len(invalid_fields) > 0:
            e = Exception("One or more invalid fields in config file:")
            for name, d in invalid_fields:
                e.add_note(f"  {name}: {str(d)}")
            e.add_note("Please edit your config file:")
            e.add_note(f"{self.location}")
            raise e
