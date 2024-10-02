import shutil
import simfile
from collections import Counter
from pathlib import Path
from simfile.dir import SimfilePack
from tempfile import TemporaryDirectory
from typing import Optional
from ._utils import (
    delete_macos_files,
    get_charts_string,
    print_simfile_data,
    prompt_overwrite,
    setup_working_dir,
    simfile_paths,
)


def add_pack(
    path_or_url: str,
    packs: Path,
    courses: Path,
    downloads: Optional[Path] = None,
    overwrite: bool = False,
    delete_macos_files_flag: bool = False,
) -> None:
    """
    Takes a path to a local directory or a path/url to an archive and adds the
    contained pack to `packs`. Supplied local files are not moved.

    In the case of multiple valid pack directories (multiple folders containing
    .sm files with different direct parents), a warning will be printed, and the
    pack containing the most songs will be added.

    If there is already an existing pack in `settings.packs` with the same name,
    the user will be prompted to overwrite or keep the existing file. If the
    `overwrite` kwarg is set to true, this check is skipped and the pack is
    overwritten without this check.
    """
    with TemporaryDirectory() as temp_directory:
        working_dir = setup_working_dir(path_or_url, Path(temp_directory), downloads)

        # 2nd parent of a simfile path is a valid pack directory
        # pack_dir_counts stores the # of simfiles in each pack
        pack_dir_counts = Counter(
            map(lambda p: p.parents[1], simfile_paths(working_dir))
        )
        if len(pack_dir_counts) == 0:
            raise Exception("No packs found.")
        elif len(pack_dir_counts) > 1:
            print("Warning | Multiple pack directories found:")
            packs_by_frequency = pack_dir_counts.most_common()
            for pack, count in packs_by_frequency:
                print(f"{pack.relative_to(working_dir)} ({count} songs)")
            pack_path = packs_by_frequency[0][0]
            print(
                f"Selecting pack with the most songs: {pack_path.relative_to(working_dir)}"
            )
        else:
            pack_path, _ = pack_dir_counts.popitem()

        if delete_macos_files_flag:
            delete_macos_files(pack_path)
        pack = SimfilePack(pack_path)
        songs = list(pack.simfiles(strict=False))

        # print pack metadata
        print(f"{pack.name} contains {len(songs)} songs:")
        for song in songs:
            print(f"  {get_charts_string(song)} {song.title} ({song.artist})")

        # check if pack already exists
        dest = packs.joinpath(pack_path.name)
        if dest.exists():
            if not overwrite:
                if delete_macos_files_flag:
                    delete_macos_files(dest)
                existing_pack = SimfilePack(dest)
                existing_songs = list(existing_pack.simfiles())
                diff = len(existing_songs) - len(songs)
                if diff > 0:
                    print(f"Prompt: Pack already exists with {diff} fewer songs.")
                elif diff < 0:
                    print(f"Prompt: Pack already exists with {-diff} more songs.")
                else:  # difference == 0
                    print("Prompt: Pack already exists with the same number of songs.")
                if not prompt_overwrite("pack"):
                    exit(1)
            shutil.rmtree(dest)

        # look for a Courses folder countaining .crs files
        num_courses = 0
        courses_subfolder = courses.joinpath(pack.name)
        courses_subfolder.mkdir(exist_ok=True)
        crs_parent_dirs = set(map(lambda p: p.parent, working_dir.rglob("*.crs")))
        for crs_parent_dir in crs_parent_dirs:
            for file in filter(Path.is_file, crs_parent_dir.iterdir()):
                file.replace(courses_subfolder.joinpath(file.name))
                if file.suffix == ".crs":
                    num_courses += 1
        # move pack to packs directory
        shutil.move(pack_path, dest)

    # Print success message
    if num_courses == 1:
        print(f"Added {pack.name} with {len(songs)} songs and 1 course.")
    else:
        print(f"Added {pack.name} with {len(songs)} songs and {num_courses} courses.")


def add_song(
    path_or_url: str,
    singles: Path,
    cache: Path,
    downloads: Optional[Path] = None,
    overwrite: bool = False,
    delete_macos_files_flag: bool = False,
):
    """
    Takes a path to a local directory or a path/url to an archive and adds the
    contained song to `singles`. Supplied local files are not changed/moved.

    In the case of multiple valid songs (multiple folders containing
    .sm files), an exception will be raised.

    If there is already an existing song in `settings.singles` with the same
    folder name, the user will be prompted to overwrite or keep the existing
    file. If the `overwrite` kwarg is set to true, this check is skipped and
    the song is overwritten without this check.
    """
    with TemporaryDirectory() as temp_directory:
        working_dir = setup_working_dir(path_or_url, Path(temp_directory), downloads)
        simfile_dirs = set(map(lambda p: p.parent, simfile_paths(working_dir)))

        # Ensure only one simfile was supplied
        if len(simfile_dirs) == 1:
            simfile_root = simfile_dirs.pop()
        elif len(simfile_dirs) == 0:
            raise Exception("No simfiles found.")
        else:
            # TODO: Maybe this behavior should be changed?
            # Sticking with it for now because it's simpler.
            e = Exception("More than one simfile in supplied link/directory")
            e.add_note("Supply songs individually or use add-pack instead.")
            raise e

        dest = singles.joinpath(simfile_root.name)

        # Overwrite if needed
        if dest.exists():
            if not overwrite:
                print("Prompt: A folder with the same name already exists.")
                if delete_macos_files_flag:
                    delete_macos_files(dest)
                    delete_macos_files(simfile_root)
                old = simfile.opendir(dest, strict=False)[0]
                new = simfile.opendir(simfile_root, strict=False)[0]
                print_simfile_data(old, "Old Simfile")
                print_simfile_data(new, "New Simfile")
                if not prompt_overwrite("simfile"):
                    exit(1)
            shutil.rmtree(dest)
            # Delete cache entry if it exists
            cache_entry_name = f"Songs_{singles.name}_{simfile_root.name}"
            cache.joinpath("Songs", cache_entry_name).unlink(missing_ok=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(simfile_root, dest)
    if delete_macos_files_flag:
        delete_macos_files(simfile_root)
    sm = simfile.opendir(dest, strict=False)[0]
    print(f"Added {sm.title} to {singles.name}.")


def censor(path: Path, packs: Path, cache: Path):
    """
    Moves the song in the supplied `path` to `censored`, hiding it from
    players. `path` must be a subdirectory of `packs` or an exception
    will be raised.
    """
    path = path.absolute()
    # Validate supplied path to sm folder
    if not path.exists():
        raise Exception(f"Error: {str(path)} does not exist")
    if not path.is_relative_to(packs):
        raise Exception(
            f"Supplied path ({path}) is not a subdirectory of settings.packs ({packs})"
        )
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


def uncensor(packs: Path):
    """
    Lists the songs in `settings.censored` and prompts the user to choose one to
    uncensor. The uncensored file will be moved back to its original location
    in settings.packs.
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
