import sys
import typer
import itg_cli
from pathlib import Path
from rich import print, panel
from typing import Annotated, Optional, TypeAlias
from itg_cli._config import CLISettings

DEFAULT_CONFIG_PATH = Path(typer.get_app_dir("itg-cli")) / "config.toml"
ConfigOption: TypeAlias = Annotated[
    Path, typer.Option("--config", help="path to a .toml config file")
]
OverwriteOption: TypeAlias = Annotated[
    bool,
    typer.Option(
        help="automatically accept overwrite confirmation",
    ),
]
cli = typer.Typer()


@cli.command("init-config")
def init_config(
    path: Annotated[Optional[Path], typer.Argument()] = DEFAULT_CONFIG_PATH,
):
    cfg = CLISettings(path, write_default=True)
    print(
        panel.Panel(
            f"Initialized config: [white]{str(cfg.location)}",
            style="green",
        )
    )


@cli.command("add-pack")
def add_pack(
    path_or_url: str,
    config_path: ConfigOption = DEFAULT_CONFIG_PATH,
    overwrite: OverwriteOption = False,
):
    """Add a pack from a supplied link or path."""
    config = CLISettings(config_path)
    itg_cli.add_pack(
        path_or_url,
        config.packs,
        config.courses,
        downloads=config.downloads,
        overwrite=overwrite,
        delete_macos_files_flag=config.delete_macos_files,
    )


@cli.command("add-song")
def add_song(
    path_or_url: str,
    config_path: ConfigOption = DEFAULT_CONFIG_PATH,
    overwrite: OverwriteOption = False,
):
    """Add a song from a supplied link or path to your configured Singles pack."""
    config = CLISettings(config_path)
    itg_cli.add_pack(
        path_or_url,
        config.packs,
        config.courses,
        downloads=config.downloads,
        overwrite=overwrite,
        delete_macos_files_flag=config.delete_macos_files,
    )


@cli.command()
def censor(path: Path, config_path: ConfigOption = DEFAULT_CONFIG_PATH):
    """Moves a song (subdirectory of your singles path) to your"""
    config = CLISettings(config_path)
    itg_cli.censor(path, config.packs, config.censored, config.cache)


@cli.command()
def uncensor(config_path: ConfigOption = DEFAULT_CONFIG_PATH):
    config = CLISettings(config_path)
    itg_cli.uncensor(config.censored, config.packs)


def main():
    # Check config and create default config if none supplied
    if "init-config" not in sys.argv and not DEFAULT_CONFIG_PATH.exists():
        init_config(DEFAULT_CONFIG_PATH)
    cli()


if __name__ == "__main__":
    main()
