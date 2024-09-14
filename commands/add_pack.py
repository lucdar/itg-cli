import os
import shutil
from simfile.dir import SimfilePack
from .utils.download_file import download_file
from .utils.add_utils import (
    cleanup,
    validate_path,
    move_to_temp,
    find_simfile_dirs,
    delete_macos_files,
    get_charts_string,
    prompt_overwrite,
)
from config import settings

TEMP_ROOT = settings.temp
PACKS = settings.packs
COURSES = settings.courses


def add_pack(args):
    # create random temp subdirectory directory name
    TEMP = os.path.join(TEMP_ROOT, os.urandom(8).hex())

    # clear temp directory if not empty
    cleanup(TEMP)

    # download file if URL
    if args.path.startswith("http"):
        path = download_file(args.path)
        # print("path to download:", path)
    else:
        path = os.path.abspath(args.path)

    validate_path(path, TEMP)
    move_to_temp(path, TEMP)

    # identify simfile paths
    sm_dirs = find_simfile_dirs(TEMP)
    if len(sm_dirs) == 0:
        cleanup(TEMP)
        raise Exception("No valid simfiles found")
    if len(sm_dirs) == 1:
        # TODO: Exit in this case
        print("Warning: Only one valid simfile found. Did you mean to use add-song?")
    pack_dirs = []
    for sm_dir in sm_dirs:
        sm_dir = os.path.dirname(sm_dir)
        pack_dirs.append(sm_dir)

    # check for multiple valid pack directories
    # this usually won't happen, but sometimes "secret" simfiles can cause this
    # or i guess multiple packs bundled together?
    pack_dirs = list(set(pack_dirs))
    if len(pack_dirs) > 1:
        # TODO: Default to picking dir with most
        # Print warning that multiple valid pack directories were found
        print("Prompt: Multiple valid pack directories found:")
        pack_dirs = sorted(pack_dirs, key=len)
        for i, pack_dir in enumerate(pack_dirs, start=1):
            print(f"{i}. {pack_dir}")
        while True:
            print("Please choose a pack directory to proceed with: ", end="")
            choice = input()
            if choice.isdigit() and int(choice) in range(0, len(pack_dirs)):
                print(f"Chosen dir: {pack_dirs[int(choice) - 1]}")
                pack_dirs = [pack_dirs[int(choice) - 1]]
                break
            else:
                print("Invalid choice. Please choose again.")

    if settings.delete_macos_files:  # delete macos files if enabled
        delete_macos_files(pack_dirs[0])

    pack = SimfilePack(pack_dirs[0])
    songs = list(pack.simfiles())

    # print pack metadata
    print(f"{pack.name} contains {len(songs)} songs:")
    for song in songs:
        print(f"  {get_charts_string(song)} {song.title} ({song.artist})")

    # check if pack already exists
    dest = os.path.join(PACKS, pack.name)
    if os.path.exists(dest):
        if settings.delete_macos_files:  # delete macos files if enabled
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
        if "overwrite" not in args:
            prompt_overwrite("pack", TEMP)
        shutil.rmtree(dest)

    # look for a Courses folder countaining .crs files
    added_courses = False
    crs_dirs = []
    for root, _, files in os.walk(TEMP):
        for file in files:
            if file.endswith(".crs") and "Courses" in root:
                crs_dirs.append(os.path.join(root, file))
    if len(crs_dirs) > 0:
        print(f"Found {len(crs_dirs)} courses:")
        for crs in crs_dirs:
            print(f"  {os.path.basename(crs)}")
        if COURSES != "":
            # copy all files in directories with .crs files to courses subfolder
            # course banners are not .crs files
            courses_subfolder = os.path.join(COURSES, pack.name)
            if os.path.exists(courses_subfolder):
                shutil.rmtree(courses_subfolder)
            os.mkdir(courses_subfolder)
            # containing folders for courses
            courses_dirs = [os.path.dirname(crs) for crs in crs_dirs]
            courses_dirs_set = set(courses_dirs)
            for courses_dir in courses_dirs_set:
                for file in os.listdir(courses_dir):
                    file_dir = os.path.join(courses_dir, file)
                    if os.path.isfile(file_dir):
                        shutil.copy(file_dir, courses_subfolder)
            added_courses = True

    # move pack to packs directory
    shutil.move(pack.pack_dir, os.path.join(PACKS, pack.name))
    print(f"Added pack {'and courses ' if added_courses else ''}successfully!")
    cleanup(TEMP)
