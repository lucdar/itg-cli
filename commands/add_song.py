import shutil
import simfile
from config import CLISettings
from pathlib import Path
from tempfile import TemporaryDirectory
from .utils.add_utils import (
    setup_working_dir,
    simfile_paths,
    delete_macos_files,
    print_simfile_data,
    prompt_overwrite,
)


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
