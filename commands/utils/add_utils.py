import os
import shutil
from pathlib import Path
from itertools import chain
from typing import Iterable
from simfile.types import Simfile, Chart
from .download_file import download_file


def simfile_paths(path: Path) -> Iterable[Path]:
    """
    Returns an iterator of valid paths to .sm or .ssc files that start with
    `path`. Paths that contain __MACOSX folders or whose simfiles begin with
    `.` are filtered.
    """

    def path_filter(p: Path):
        return not ("__MACOSX" in p.parts or p.name.startswith("."))

    sms = path.rglob("*.sm")
    sscs = path.rglob("*.ssc")
    return filter(path_filter, chain(sms, sscs))


def print_simfile_data(sm: Simfile, label: str = "data") -> None:
    """Prints simfile data"""
    print(
        f"### {label} ###",
        "  Title: " + sm.title,
        " Artist: " + sm.artist,
        " Meters: " + str(get_charts_string(sm)),
        sep="\n",
        end="\n\n",
    )


def get_charts_as_ints(sm: Simfile, default: int = 0) -> list[int]:
    """
    Returns a list of charts as integers.
    If the meter in the simfile is not a number, it will be replaced with the `default` value.
    """
    charts = sm.charts

    def getMeter(c: Chart):
        if c.meter.isdigit():
            return int(c.meter)
        else:
            return default

    return [getMeter(chart) for chart in charts]


def get_charts_string(sm: Simfile, difficulty_labels: bool = False) -> str:
    """
    Returns the string representation of chart meters of a simfile (with quotes removed).
    Also includes the difficulty label if `difficulty_labels` is True.

    Example:
        get_charts_string(sm) -> "[5, 7, 10, 12]"
        get_charts_string(sm, difficulty_labels=True) -> "[Easy 5, Medium 7, Hard 10, Challenge 12]"
    """

    def fn(c: Chart):
        if difficulty_labels:
            return f"{c.difficulty} {c.meter}"
        else:
            return c.meter

    return str([fn(c) for c in sm.charts]).replace("'", "")


def delete_macos_files(path: str) -> None:
    """Deletes all `._` files in the supplied path"""
    for root, _, files in os.walk(path):
        for file in files:
            if file.startswith("._"):
                os.remove(os.path.join(root, file))


def extract(archive_path: Path) -> Path:
    """
    Extracts an archive to a containing folder in the same directory.
    Returns the path to the containing folder.

    Uses shutil.unpack_archive, and thus only supports the following formats:
    `zip, tar, gztar, bztar, xztar`
    """
    dest = archive_path.with_suffix("")
    dest.mkdir()
    print("Extracting archive...")
    shutil.unpack_archive(archive_path, dest)
    return dest


def prompt_overwrite(item: str) -> bool:
    """
    Prompts the user to overwrite the existing `item`.
    Overwriting returns `True`, Keeping returns `False`.
    """
    while True:
        print(f"Overwrite existing {item}? [Y/n] ", end="")
        match input().lower():
            case "y" | "":
                print(f"Overwriting exisiting {item}.")
                return True
            case "n":
                print(f"Keeping existing {item}.")
                return False
            case _:
                print("Invalid choice")


def setup_working_dir(path_str: str, downloads: Path, temp: Path) -> Path:
    """
    Takes the supplied parameter for an add command and does any necessary
    extraction/downloading. Moves the directory to temp if it was downloaded
    or extracted; copies if supplied as a path to a local directory instead.
    """
    downloaded, extracted = False, False
    if path_str.startswith("http"):
        path = download_file(path_str, downloads)
        downloaded = True
    else:
        path = Path(path_str).absolute()
    if not path.exists():
        raise Exception("Path does not exist:", str(path))
    if not path.is_dir():
        path = extract(path)
        extracted = True
    working_path = temp.joinpath(path.name)
    if downloaded or extracted:
        shutil.move(path, working_path)
    else:
        shutil.copy(path, working_path)
    return working_path
