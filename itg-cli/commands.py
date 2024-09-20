import shutil
import simfile
from collections import Counter
from config import CLISettings
from pathlib import Path
from simfile.dir import SimfilePack
from tempfile import TemporaryDirectory
from utils import (
    delete_macos_files,
    get_charts_string,
    print_simfile_data,
    prompt_overwrite,
    setup_working_dir,
    simfile_paths,
)


def add_pack(args, settings: CLISettings):
    with TemporaryDirectory() as temp_directory:
        working_dir = setup_working_dir(
            args.path, settings.downloads, Path(temp_directory)
        )

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

        if settings.delete_macos_files:
            delete_macos_files(pack_path)
        pack = SimfilePack(pack_path)
        songs = list(pack.simfiles(strict=False))

        # print pack metadata
        print(f"{pack.name} contains {len(songs)} songs:")
        for song in songs:
            print(f"  {get_charts_string(song)} {song.title} ({song.artist})")

        # check if pack already exists
        dest = settings.packs.joinpath(pack_path.name)
        if dest.exists():
            if not args.overwrite:
                if settings.delete_macos_files:
                    delete_macos_files(dest)
                existing_pack = SimfilePack(dest)
                existing_songs = list(existing_pack.simfiles())
                diff = len(songs) - len(existing_songs)
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
        courses_subfolder = settings.courses.joinpath(pack.name)
        courses_subfolder.mkdir(exist_ok=True)
        crs_parent_dirs = set(map(lambda p: p.parent, working_dir.rglob("*.crs")))
        for crs_parent_dir in crs_parent_dirs:
            for file in filter(Path.is_file, crs_parent_dir.iterdir()):
                file.replace(courses_subfolder.joinpath(file.name))
                if file.suffix == ".crs":
                    num_courses += 1
        # move pack to packs directory
        pack_path.rename(dest)

    # Print success message
    if num_courses == 1:
        print(f"Added {pack.name} with {len(songs)} songs and 1 course.")
    else:
        print(f"Added {pack.name} with {len(songs)} songs and {num_courses} courses.")


def add_song(args, settings: CLISettings):
    with TemporaryDirectory() as temp_directory:
        working_dir = setup_working_dir(
            args.path, settings.downloads, Path(temp_directory)
        )
        simfile_dirs = set(map(lambda p: p.parent, simfile_paths(working_dir)))

        # Ensure only one simfile was supplied
        if len(simfile_dirs) == 1:
            simfile_root = simfile_dirs.pop()
        elif len(simfile_dirs) == 0:
            raise Exception("No simfiles found.")
        else:
            # TODO: Maybe this behavior should be changed? Sticking with it for now because it's simpler.
            raise Exception(
                "More than one simfile in supplied link/directory"
            ).add_note("Supply songs individually or use add-pack instead.")

        dest = settings.singles.joinpath(simfile_root.name)

        # Overwrite if needed
        if dest.exists():
            if not args.overwrite:
                print("Prompt: A folder with the same name already exists.")
                if settings.delete_macos_files:
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
            cache_entry_name = f"Songs_{settings.singles.name}_{simfile_root.name}"
            settings.cache.joinpath("Songs", cache_entry_name).unlink(missing_ok=True)
        simfile_root.rename(dest)
    if settings.delete_macos_files:
        delete_macos_files(simfile_root)
    sm = simfile.opendir(dest, strict=False)[0]
    print(f"Added {sm.title} to {settings.singles.name}.")


def censor(args, settings: CLISettings):
    path = Path(args.path).absolute()
    # Validate supplied path to sm folder
    if not path.exists():
        raise Exception(f"Error: {str(path)} does not exist")
    if not path.is_relative_to(settings.packs):
        raise Exception(
            f"Supplied path ({path}) is not a subdirectory of settings.packs ({settings.packs})"
        )
    try:
        sm, _ = simfile.opendir(path, strict=False)
    except Exception as e:
        raise Exception(f"Error: {path} is not a valid simfile directory: {e}")

    # Move the simfile to the censored folder under the same pack subdirectory
    pack_and_song = path.relative_to(settings.packs)
    destination = settings.censored.joinpath(pack_and_song)
    shutil.move(path, destination)

    # Remove the song's cache entry if it exists
    cache_entry_name = f"Songs_{path.name}_{path.parent.name}"
    settings.cache.joinpath("Songs", cache_entry_name).unlink(missing_ok=True)

    print(f"Censored {sm.title} from {path.parent.name}.")


def uncensor(settings: CLISettings):
    # List the simfile_paths that are currently censored and build a list of choices
    simfile_paths: list[Path] = []
    for pack in filter(Path.is_dir, settings.censored.iterdir()):
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
    pack_and_song = chosen_path.relative_to(settings.censored)
    destination = settings.packs.joinpath(pack_and_song)
    shutil.move(chosen_path, destination)

    sm, _ = simfile.opendir(destination)
    print(f"Uncensored {sm.title} from {destination.parent.name}.")
