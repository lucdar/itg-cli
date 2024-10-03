import sys
import typer
import itg_cli
from pathlib import Path
from rich import panel, print, prompt
from typing import Annotated, Optional, TypeAlias
from itg_cli import __version__
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
cli = typer.Typer(no_args_is_help=True)


@cli.command("init-config")
def init_config(
    path: Annotated[Optional[Path], typer.Argument()] = DEFAULT_CONFIG_PATH,
):
    """Write a config file with default values to the supplied directory or the default config path. Prompts to overwrite existing config if it exists."""
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
    """Move a song in your packs folder to a (configurable) hidden folder."""
    config = CLISettings(config_path)
    itg_cli.censor(path, config.packs, config.censored, config.cache)


@cli.command()
def uncensor(config_path: ConfigOption = DEFAULT_CONFIG_PATH):
    """Display a list of censored songs and prompts you to select one to uncensor."""
    config = CLISettings(config_path)
    itg_cli.uncensor(config.censored, config.packs)


def version_callback(run: bool):
    if run:
        print(f"itg-cli version {__version__}")
        raise typer.Exit()


@cli.callback()
def typer_entry(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Display the version and exit.",
        ),
    ] = False,
):
    # Check config and create default config if none supplied
    if "init-config" not in sys.argv and not DEFAULT_CONFIG_PATH.exists():
        init_config(DEFAULT_CONFIG_PATH)


if __name__ == "__main__":
    cli()
