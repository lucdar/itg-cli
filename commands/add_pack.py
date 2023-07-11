import json
import os
import shutil
import simfile
from simfile.types import Simfile
from simfile.dir import SimfilePack
from .utils.download_file import download_file
from .utils.add_utils import cleanup, extract_archive, find_simfile_dirs, get_charts_string
from .utils.constants import TEMP_ROOT, PACKS


def add_pack(args):
    # create random temp subdirectory directory name
    TEMP = os.path.join(TEMP_ROOT, os.urandom(8).hex())

    # clear temp directory if not empty
    cleanup(TEMP)

    # download file if URL
    if args.path.startswith('http'):
        path = download_file(args.path)
        # print("path to download:", path)
    else:
        path = args.path

    # validate path
    if path is None:
        raise Exception('No path supplied')
    elif os.path.exists(path) is False:
        raise Exception('Invalid path:', path)
    elif os.path.isdir(path):  # copy song if directory
        shutil.copytree(path, TEMP)
    else:  # extract archive to temp directory
        os.mkdir(TEMP)
        try:
            extract_archive(path, TEMP)
        except:
            cleanup(TEMP)
            raise Exception('Error extracting archive')

    # identify simfile paths
    sm_dirs = find_simfile_dirs(TEMP)
    if len(sm_dirs) == 0:
        cleanup(TEMP)
        raise Exception('No valid simfiles found')
    if len(sm_dirs) == 1:
        print('Warning: Only one valid simfile found. Did you mean to use add-song?')
    pack_dirs = []
    for sm_dir in sm_dirs:
        sm_dir = os.path.dirname(sm_dir)
        pack_dirs.append(sm_dir)

    # check for multiple valid pack directories
    # this usually won't happen, but sometimes "secret" simfiles can cause this
    # or i guess multiple packs bundled together?
    pack_dirs_set = set(pack_dirs)
    if len(pack_dirs_set) > 1:
        print('Multiple valid pack directories found:')
        pack_dirs_count = {}
        for candidate in pack_dirs_set:
            pack_dirs_count[candidate] = pack_dirs.count(candidate)
        print(pack_dirs_count)
        # TODO: prompt user to choose a pack directory
        raise NotImplementedError('Multiple valid pack directories found')

    pack = SimfilePack(pack_dirs[0])
    songs = list(pack.simfiles())

    # print pack metadata
    print(f"{pack.name} contains {len(songs)} songs:")
    for song in songs:
        print(f"  {get_charts_string(song)} {song.title} ({song.artist})")
    while True:
        print("Prompt: Do you want to add this pack? [Y/n] ", end="")
        choice = input().lower()
        if choice == 'y':
            break
        elif choice == 'n':
            cleanup(TEMP)
            return
        else:
            print('Invalid choice')

    # check if pack already exists
    dest = os.path.join(PACKS, pack.name)
    if os.path.exists(dest):
        existing_pack = SimfilePack(dest)
        existing_songs = list(existing_pack.simfiles())
        difference = len(songs) - len(existing_songs)
        if difference == 0:
            print('Pack already exists (with the same number of songs).')
        elif difference > 0:
            print(f"Pack already exists with {difference} fewer songs.")
        else:  # difference < 0
            print(f"Pack already exists with {abs(difference)} more songs.")
        while True:
            print('Prompt: Pack already exists.')
            print('[O]verwrite or keep [E]xisting pack? ', end='')
            choice = input().lower()
            if choice == 'o':
                shutil.rmtree(dest)
                break
            elif choice == 'e':
                cleanup(TEMP)
                return
            else:
                print('Invalid choice')

    # move pack to packs directory
    shutil.move(pack.pack_dir, os.path.join(PACKS, pack.name))
    cleanup(TEMP)
