import shutil
import simfile
from collections import Counter
from pathlib import Path
from simfile.dir import SimfilePack
from simfile.types import Simfile
from tempfile import TemporaryDirectory
from typing import Callable, Optional, TypeAlias
from itg_cli._utils import (
    delete_macos_files,
    setup_working_dir,
    simfile_paths,
)

PackOverwriteHandler: TypeAlias = Callable[[SimfilePack, SimfilePack], bool]
SongOverwriteHandler: TypeAlias = Callable[
    [tuple[Simfile, str], tuple[Simfile, str]], bool
]


def add_pack(
    path_or_url: str,
    packs: Path,
    courses: Path,
    downloads: Optional[Path] = None,
    overwrite: PackOverwriteHandler = lambda _new, _old: False,
    delete_macos_files_flag: bool = False,
) -> tuple[SimfilePack, int]:
    """
    Takes a path to a local directory or a path/url to an archive and adds the
    contained pack to `packs`. Supplied local files are not moved.

    In the case of multiple valid pack directories (multiple folders
    containing .sm files with different direct parents), a warning will be
    displayed, and the pack containing the most songs will be added.

    If there is already an existing pack in `settings.packs` with the same
    name, the user will be prompted to overwrite or keep the existing file. If
    the `overwrite` kwarg is set to true, this check is skipped and the pack
    is overwritten without this check.

    Returns:
        a tuple containing a `SimfilePack` object of the added pack and the
        number of courses added.
    """
    with TemporaryDirectory() as temp_directory:
        working_dir = setup_working_dir(
            path_or_url, Path(temp_directory), downloads
        )

        # 2nd parent of a simfile path is a valid pack directory
        # pack_dir_counts stores the # of simfiles in each pack
        pack_dir_counts = Counter(
            p.parents[1] for p in simfile_paths(working_dir)
        )

        if len(pack_dir_counts) == 0:
            raise Exception("No packs found.")
        elif len(pack_dir_counts) > 1:
            print("Warning | Multiple pack directories found:")
            packs_by_frequency = pack_dir_counts.most_common()
            for pack, count in packs_by_frequency:
                print(f"{pack.relative_to(working_dir)} ({count} songs)")
            pack_path, _ = packs_by_frequency[0]
            rel_path = pack_path.relative_to(working_dir)
            print(f"Selecting pack with the most songs: {rel_path}")
        else:
            pack_path, _ = pack_dir_counts.popitem()

        if delete_macos_files_flag:
            delete_macos_files(pack_path)
        pack = SimfilePack(pack_path)
        songs = list(pack.simfiles(strict=False))

        # check if pack already exists
        dest = packs.joinpath(pack_path.name)
        if dest.exists():
            if delete_macos_files_flag:
                delete_macos_files(dest)
            if not overwrite(pack, SimfilePack(dest)):
                exit(1)
            shutil.rmtree(dest)

        # look for a Courses folder countaining .crs files
        num_courses = 0
        courses_subfolder = courses.joinpath(pack.name)
        courses_subfolder.mkdir(exist_ok=True)
        crs_parent_dirs = {p.parent for p in working_dir.rglob("*.crs")}
        for crs_parent_dir in crs_parent_dirs:
            for file in filter(Path.is_file, crs_parent_dir.iterdir()):
                file.replace(courses_subfolder.joinpath(file.name))
                if file.suffix == ".crs":
                    num_courses += 1

        shutil.move(pack_path, dest)
        return SimfilePack(dest), num_courses


def add_song(
    path_or_url: str,
    singles: Path,
    cache: Path,
    downloads: Optional[Path] = None,
    overwrite: SongOverwriteHandler = lambda _new, _old: False,
    delete_macos_files_flag: bool = False,
) -> tuple[Simfile, str]:
    """
    Takes a path to a local directory or a path/url to an archive and adds the
    contained song to `singles`. Supplied local files are not changed/moved.

    In the case of multiple valid songs (multiple folders containing
    .sm files), an exception will be raised.

    If there is already an existing song in `settings.singles` with the same
    folder name, the user will be prompted to overwrite or keep the existing
    file. If the `overwrite` kwarg is set to true, this check is skipped and
    the song is overwritten without this check.

    Returns:
        a tuple containing the Simfile object of the added song and the path
        to the .sm/.ssc containing the chart data.
    """
    with TemporaryDirectory() as temp_directory:
        working_dir = setup_working_dir(
            path_or_url, Path(temp_directory), downloads
        )
        simfile_dirs = {p.parent for p in simfile_paths(working_dir)}

        # Ensure only one simfile was supplied
        if len(simfile_dirs) == 1:
            simfile_root = simfile_dirs.pop()
        elif len(simfile_dirs) == 0:
            raise Exception("No simfiles found.")
        else:
            # TODO: Maybe this behavior should be changed?
            # Sticking with it for now because it's simpler.
            raise Exception(
                "More than one simfile in supplied link/directory\n"
                + "Supply songs individually or use add-pack instead."
            )

        dest = singles.joinpath(simfile_root.name)

        if dest.exists():
            if delete_macos_files_flag:
                delete_macos_files(simfile_root)
                delete_macos_files(dest)
            new = simfile.opendir(simfile_root, strict=False)
            old = simfile.opendir(dest, strict=False)
            if not overwrite(new, old):
                exit(1)
            shutil.rmtree(dest)
            # Delete cache entry if it exists
            cache_entry = "_".join(
                [singles.parent.name, singles.name, simfile_root.name]
            )
            cache.joinpath("Songs", cache_entry).unlink(missing_ok=True)

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(simfile_root, dest)
    if delete_macos_files_flag:
        delete_macos_files(simfile_root)

    return simfile.opendir(dest, strict=False)


def censor(path: Path, packs: Path, cache: Path) -> None:
    """
    Moves the song in the supplied `path` to `packs`/.censored, hiding it from
    players. `path` must be a subdirectory of `packs` or an exception
    will be raised.
    """
    path = path.absolute()
    # Validate supplied path to sm folder
    if not path.exists():
        raise Exception(f"Error: {str(path)} does not exist")
    if not path.is_relative_to(packs):
        raise Exception(f"Supplied path {path} is not a pack in {packs}")
    try:
        sm, _ = simfile.opendir(path, strict=False)
    except Exception as e:
        raise Exception(f"{path} is not a valid simfile directory: {e}")

    # Move the simfile to the censored folder under the same pack subdirectory
    pack_and_song = path.relative_to(packs)
    destination = packs / ".censored" / pack_and_song
    shutil.move(path, destination)

    # Remove the song's cache entry if it exists
    cache_entry_name = f"Songs_{path.name}_{path.parent.name}"
    cache.joinpath("Songs", cache_entry_name).unlink(missing_ok=True)

    print(f"Censored {sm.title} from {path.parent.name}.")


def uncensor(packs: Path) -> None:
    """
    Lists the songs in `settings.censored` and prompts the user to choose one
    to uncensor. The uncensored file will be moved back to its original
    location in settings.packs.
    """
    # TODO: make this command more module-friendly
    censored = packs / ".censored"
    simfile_paths: list[Path] = []
    for pack in filter(Path.is_dir, censored.iterdir()):
        for simfile_path in filter(Path.is_dir, pack.iterdir()):
            sm, _ = simfile.opendir(simfile_path)
            simfile_paths.append(simfile_path)
            print(f"{len(simfile_paths)}. {sm.title} ({pack.name})")
    if len(simfile_paths) == 0:
        print("No censored songs")
        exit()

    print(f"Select a song to uncensor (1-{len(simfile_paths)}): ", end="")
    while True:
        user_input = input()
        choice = int(user_input) if user_input.isdigit() else 0
        if choice - 1 in range(len(simfile_paths)):
            break
        else:
            print("Invalid choice. Please choose again.")

    chosen_path = simfile_paths[choice - 1]
    pack_and_song = chosen_path.relative_to(censored)
    destination = packs.joinpath(pack_and_song)
    shutil.move(chosen_path, destination)

    sm, _ = simfile.opendir(destination)
    print(f"Uncensored {sm.title} from {destination.parent.name}.")
