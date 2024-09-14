import os
import shutil
from simfile.types import Simfile, Chart


def extract_archive(path: str, dest: str) -> None:
    """Extracts an archive to the supplied destination"""
    # TODO: add support for other archive types.
    shutil.unpack_archive(path, dest)


def find_simfile_dirs(path: str) -> list[str]:
    """Returns a list of valid simfile directories in the supplied path"""
    dirs = set()
    for root, _, files in os.walk(path):
        if "__MACOSX" in root:  # ignore macosx folders
            continue
        for file in files:
            if file.startswith("."):  # ignore hidden files
                continue
            if file.endswith(".sm") or file.endswith(".ssc"):
                # File found in this directory, continue to next directory
                dirs.add(root)
                break
    return list(dirs)


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

        def fn(c):
            return f"{c.difficulty} {c.meter}"
    else:

        def fn(c):
            return c.meter

    return str(list(map(fn, charts))).replace("'", "")


def delete_macos_files(path: str) -> None:
    """Deletes all `._` files in the supplied path"""
    for root, _, files in os.walk(path):
        for file in files:
            if file.startswith("._"):
                os.remove(os.path.join(root, file))


def move_to_temp(path: str, working_dir: str):
    """Moves the files supplied by path to the working_dir directory. Extracts archives if necessary."""
    # TODO: bro what was i cooking.....
    if os.path.isdir(path):  # copy song if directory
        folder = os.path.basename(os.path.normpath(path))
        dest = os.path.join(working_dir, folder)
        shutil.copytree(path, dest)
    else:
        # Attempt to extract archive
        try:
            extract_archive(path, working_dir)
        except Exception as e:
            raise Exception("Error extracting archive: ", e)


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
                break
            case "n":
                print(f"Keeping existing {item}.")
            case _:
                print("Invalid choice")
