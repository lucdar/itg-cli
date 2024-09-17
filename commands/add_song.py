import os
import shutil
import simfile
from pathlib import Path
from tempfile import TemporaryDirectory
from .utils.download_file import download_file
from .utils.add_utils import (
    extract,
    simfile_paths,
    delete_macos_files,
    print_simfile_data,
    prompt_overwrite,
)


def add_song(args, settings):
    with Path(TemporaryDirectory()) as temp_directory:
        if args.path.startswith("http"):
            path = download_file(args.path, settings.downloads)
        else:
            path = Path(args.path).absolute()

        if os.path.exists(path) is False:
            raise Exception("Invalid path:", path)
        if not path.is_dir():
            path = extract(path)

        # Move files to temporary working directory
        # TODO: Maybe needs some logic for moving vs. copying?
        working_path = temp_directory.joinpath(path.name)
        path.replace(working_path)

        simfile_dirs = set(map(lambda p: p.parent, simfile_paths(working_path)))

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

        dest = Path(settings.singles).joinpath(simfile_root.name)

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
                if prompt_overwrite("simfile"):
                    exit(1)
            shutil.rmtree(dest)
            if settings.cache:  # Delete cache entry if it exists
                cache_entry_name = (
                    f"Songs_{simfile_root.name}_{Path(settings.singles).name}"
                )
                Path(settings.cache).joinpath("Songs", cache_entry_name).unlink(
                    missing_ok=True
                )

        if settings.delete_macos_files:
            delete_macos_files(simfile_root)
        sm = simfile.opendir(dest, strict=False)[0]
        simfile_root.rename(dest)
    print(f"Added {sm.title} to {settings.singles.basename}.")
