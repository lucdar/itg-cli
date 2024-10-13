import os
import platform
import tomlkit
from importlib.resources import files
from tomlkit.toml_file import TOMLFile
from typing import Optional
from pathlib import Path


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class CLISettings:
    location: Path  # The path to the .toml file
    root: Path
    singles: Path
    delete_macos_files: bool
    downloads: Optional[Path]
    packs: Path
    courses: Path
    cache: Path

    TEMPLATE_PATH = files("itg_cli").joinpath("config_template.toml")

    def __init__(self, toml: Path, write_default: bool = False):
        """
        Creates a CLI settings object based on the toml file at `toml`.

        If `toml` does not exist, creates a new .toml file with defaults based
        on the user's operating system. If default settings can not be
        inferred, warns the user, instructs them to populate the file manually,
        and exits.
        """
        self.location = toml
        if write_default:
            self.__write_default_toml(toml)
        elif not self.location.exists():
            raise FileNotFoundError(
                f"No config found at supplied path: {toml}"
            )

        # Ensure required tables and fields are present
        toml_doc = TOMLFile(toml).read()
        for table in ["required", "optional"]:
            if table not in toml_doc:
                raise ConfigError(f"Missing table ({table}) in config: {self.location}")
        required = toml_doc["required"]
        for key in ["root", "singles_pack_name", "delete_macos_files"]:
            if required.get(key) is None:
                raise ConfigError(
                    f"Required field ({key}) is empty or unbound in config: {self.location}"
                )

        # Set properties
        self.root = Path(required["root"])
        self.delete_macos_files = bool(required["delete_macos_files"])

        optional = toml_doc["optional"]
        self.downloads = (
            Path(optional["downloads"]) if optional.get("downloads") else None
        )
        self.packs = Path(optional.get("packs") or self.root / "Songs")
        self.courses = Path(optional.get("courses") or self.root / "Courses")
        self.cache = Path(optional.get("cache") or self.root / "Cache")
        self.singles = self.packs / required["singles_pack_name"]

        self.__validate_dirs()

    def __write_default_toml(self, toml: Path) -> None:
        """
        Writes a itg-cli config file to `toml` with platform-specific defaults set.
        """
        if toml.suffix != ".toml":
            raise ValueError(f"{toml} is not a .toml file.")
        template = TOMLFile(self.TEMPLATE_PATH).read()
        root, cache = None, None
        match platform.system():
            case "Windows":
                root = Path(os.getenv("APPDATA")) / "ITGmania"
            case "Linux":
                # TODO: verify/add new locations
                root = Path.home() / ".itgmania"
            case "Darwin":  # MacOS
                root = Path.home() / "Library" / "Application Support" / "ITGmania"
                cache = Path.home() / "Library" / "Caches" / "ITGmania"
            case _:
                raise ConfigError(f"Unsupported platform: {platform.system()}")
        template["required"]["root"] = tomlkit.string(str(root), literal=True)
        if cache:
            template["optional"]["cache"] = tomlkit.string(str(cache), literal=True)
        toml.parent.mkdir(parents=True, exist_ok=True)
        TOMLFile(toml).write(template)

    def __validate_dirs(self) -> None:
        """
        Ensures required directory fields exist and can be written to.
        """
        required_dirs: dict[str, Path | None] = {
            "packs": self.packs,
            "courses": self.courses,
            "cache": self.cache,
            "downloads": self.downloads,
        }
        # Conditionally add singles because it might not yet exist
        if self.singles.exists():
            required_dirs["singles"] = self.singles
        invalid = {
            name: path
            for name, path in required_dirs.items()
            if path and not (path.is_dir() and os.access(path, os.W_OK))
        }
        if invalid:
            raise ConfigError(
                "Invalid fields in config file:\n"
                + "\n".join(f"{name}: {str(path)}" for name, path in invalid.items())
                + f"\nPlease edit your config file: {self.location}"
            )
