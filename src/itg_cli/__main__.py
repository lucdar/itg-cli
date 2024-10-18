import sys
from pygments import highlight
import typer
import itg_cli
from pathlib import Path
from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from simfile.dir import SimfilePack
from simfile.types import Simfile
from typing import Annotated, Callable, Optional, TypeAlias, TypeVar
from itg_cli import __version__
from itg_cli._config import CLISettings
from itg_cli._utils import get_charts_string, prompt_overwrite

DEFAULT_CONFIG_PATH = Path(typer.get_app_dir("itg-cli")) / "config.toml"

no_highlights = Console(highlight=False)


## Overwrite Handlers ##
T = TypeVar("T")
GenericOverwriteHandler: TypeAlias = Callable[[T, T], bool]


def or_callback(
    flag: Optional[bool], callback: GenericOverwriteHandler
) -> GenericOverwriteHandler:
    """
    Returns `callback` if `flag` is None, otherwise returns a function that
    always returns `flag`
    """
    return callback if flag is None else lambda _a, _b: flag


def pack_overwrite_handler(new: SimfilePack, old: SimfilePack) -> bool:
    new_simfiles = list(new.simfiles(strict=False))
    old_simfiles = list(old.simfiles(strict=False))
    diff = len(old_simfiles) - len(new_simfiles)
    prompt = f"[bold]{new.name}[/bold] already exists (with "
    if diff > 0:
        prompt += f"{diff} fewer songs)."
    elif diff < 0:
        prompt += f"{-diff} more songs)."
    else:
        prompt += "the same number of songs)."
    no_highlights.print(prompt)
    return Confirm.ask("Overwrite existing pack?", default=True)


def song_overwrite_handler(
    new: tuple[Simfile, str], old: tuple[Simfile, str]
) -> bool:
    old_path = Path(old[1])
    pack_and_song_folder = old_path.parent.relative_to(old_path.parents[2])
    no_highlights.print(f"[bold]{pack_and_song_folder}[/] already exists.")
    return Confirm.ask("Overwrite existing simfile?", default=True)


## CLI Commands ##
cli = typer.Typer(no_args_is_help=True)
ConfigOption: TypeAlias = Annotated[
    Path, typer.Option("--config", help="path to a .toml config file")
]
OverwriteOption: TypeAlias = Annotated[
    Optional[bool],
    typer.Option(
        "--overwrite",
        "-o",
        help="automatically overwrite without confirming",
    ),
]


@cli.command("init-config")
def init_config(
    path: Annotated[Optional[Path], typer.Argument()] = DEFAULT_CONFIG_PATH,
    overwrite: OverwriteOption = False,
):
    """
    Write a config file with default values to the supplied directory or the
    default config path. Prompts to overwrite existing config if it exists.
    """
    if (
        path.exists()
        and not overwrite
        and not Confirm.ask(
            f"Overwrite existing config with default?", default=True
        )
    ):
        print(f"[green]Keeping existing config file: [bright_white]{path}")
        raise typer.Exit()
    cfg = CLISettings(path, write_default=True)
    print(
        Panel(
            f"Initialized config: [bright_white]{str(cfg.location)}",
            style="green",
        )
    )


@cli.command("add-pack")
def add_pack(
    path_or_url: Annotated[
        str, typer.Argument(help="path or URL to the pack to add")
    ],
    config_path: ConfigOption = DEFAULT_CONFIG_PATH,
    overwrite: OverwriteOption = None,
):
    """Add a pack from a supplied link or path."""
    config = CLISettings(config_path)
    pack, num_courses = itg_cli.add_pack(
        path_or_url,
        config.packs,
        config.courses,
        downloads=config.downloads,
        overwrite=or_callback(overwrite, pack_overwrite_handler),
        delete_macos_files_flag=config.delete_macos_files,
    )
    songs = list(pack.simfiles(strict=False))
    # print pack metadata
    title = " ".join(
        (
            f"\nAdded [bold green]{pack.name}[/]",
            f"with [blue]{len(songs)}[/] songs",
            f"and [blue]{num_courses}[/] {
                "courses" if num_courses != 1 else "course"
            }",
        )
    )
    columns = Columns(
        (f"[bold]{get_charts_string(song)}[/] {song.title}" for song in songs),
        expand=True,
    )
    no_highlights.print(Panel(columns, title=title))


@cli.command("add-song")
def add_song(
    path_or_url: Annotated[
        str, typer.Argument(help="path or URL to the song to add")
    ],
    config_path: ConfigOption = DEFAULT_CONFIG_PATH,
    overwrite: OverwriteOption = None,
):
    """
    Add a song from a supplied link or path to your configured Singles pack.
    """
    config = CLISettings(config_path)
    sf, loc = itg_cli.add_song(
        path_or_url,
        config.singles,
        cache=config.cache,
        downloads=config.downloads,
        overwrite=or_callback(overwrite, song_overwrite_handler),
        delete_macos_files_flag=config.delete_macos_files,
    )
    title = " ".join(
        (
            f"Added [bold green]{sf.title}[/]",
            f"to {Path(loc).parents[1].name}",
        )
    )
    content = "\n".join(
        (
            f" Title: [bold]{sf.title}[/]",
            f"Artist: [bold]{sf.artist}[/]",
            f"Charts: [bold]{
                "\n        ".join(
                    [f"[blue]{c.meter}[/] {c.description}" for c in sf.charts]
                )
            }[/]",
        )
    )

    no_highlights.print(Panel(content, title=title))


@cli.command()
def censor(
    path: Annotated[str, typer.Argument(help="path to the song to censor")],
    config_path: ConfigOption = DEFAULT_CONFIG_PATH,
):
    """
    Move a song in your packs folder to packs/.censored/Pack/Song, hiding it
    from players.
    """
    config = CLISettings(config_path)
    itg_cli.censor(Path(path), config.packs, config.cache)


@cli.command()
def uncensor(config_path: ConfigOption = DEFAULT_CONFIG_PATH):
    """
    Display a list of censored songs and prompts you to select one to
    uncensor.
    """
    config = CLISettings(config_path)
    itg_cli.uncensor(config.packs)


def version_callback(run: bool):
    if run:
        print(f"itg-cli [white][bold]{__version__}")
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
