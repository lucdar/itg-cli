import simfile
import shutil
from config import CLISettings
from pathlib import Path


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
