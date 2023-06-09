import os
import shutil
from simfile.types import Simfile, Chart


def cleanup(path) -> None:
    """Remove the supplied directory and its contents if it exists"""
    if os.path.exists(path):
        shutil.rmtree(path)


def extract_archive(path: str, dest: str) -> None:
    """Extracts an archive to the supplied destination"""
    # TODO: add support for other archive types.
    shutil.unpack_archive(path, dest)


def find_simfile_dirs(path: str) -> list[str]:
    """Returns a list of valid simfile directories in the supplied path"""
    dirs = []
    for root, _, files in os.walk(path):
        if "__MACOSX" in root:  # ignore macosx folders
            continue
        for file in files:
            if file.startswith('.'):  # ignore hidden files
                continue
            if file.endswith('.sm') or file.endswith('.ssc'):
                dirs.append(root)
                break
    return dirs


def print_simfile_data(sm: Simfile, label: str = 'data') -> None:
    """Prints simfile data"""
    print(f"### {label} ###",
          "  Title: " + sm.title,
          " Artist: " + sm.artist,
          " Meters: " + str(get_charts_string(sm)),
          sep='\n', end='\n\n')


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

    return list(map(getMeter, charts))


def get_charts_string(sm: Simfile, difficulty_labels: bool = False) -> str:
    """
    Returns the string representation of chart meters of a simfile (with quotes removed). 
    Also includes the difficulty label if `difficulty_labels` is True.

    Example:
        get_charts_string(sm) -> "[5, 7, 10, 12]"
        get_charts_string(sm, difficulty_labels=True) -> "[Easy 5, Medium 7, Hard 10, Challenge 12]"
    """
    charts = sm.charts
    if difficulty_labels:
        def fn(c): return f'{c.difficulty} {c.meter}'
    else:
        def fn(c): return c.meter
    return str(list(map(fn, charts))).replace("'", "")
