import json
import os
import shutil
import simfile
from simfile.types import Simfile
from .utils.download_file import download_file
from .utils.add_utils import *
from config import config_data

TEMP_ROOT = config_data['temp_root']
SINGLES = config_data['singles']


def print_simfile_data(sm: Simfile, label: str = 'data'):
    print(f"### {label} ###",
          "  Title: " + sm.title,
          " Artist: " + sm.artist,
          " Meters: " + str(get_charts_string(sm)).replace("'", ""),
          sep='\n', end='\n\n')


def print_simfile_choices(simfiles: list[Simfile], jsonOutput=False) -> None:
    total = len(simfiles)
    if jsonOutput:
        simfileDict = []
        for i, sm in enumerate(simfiles):
            simfile = {
                "index": i+1,
                "title": sm.title,
                "artist": sm.artist,
                "charts": get_charts_string(sm, difficulty_labels=True)
            }
            simfileDict.append(simfile)
        print(json.dumps(simfileDict, indent=4))
    else:
        for i, sm in enumerate(simfiles):
            # format chart list output
            charts = get_charts_string(sm, difficulty_labels=True)
            charts = str(charts).replace("'", "")
            indent = len(str(total)) - len(str(i+1))
            chartIndent = len(str(total)) + 3
            print(' ' * indent + f'[{i+1}] {sm.title} - {sm.artist}',
                  ' ' * chartIndent + f'{charts}',
                  sep='\n')


def add_song(args):
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

    validate_path(path, TEMP)
    move_to_temp(path, TEMP)

    # identify simfile
    print('Searching for valid simfiles...')
    sm_dirs = find_simfile_dirs(TEMP)
    if len(sm_dirs) == 0:
        cleanup(TEMP)
        raise Exception('No valid simfiles found')
    elif len(sm_dirs) == 1:
        root = sm_dirs[0]
    else:
        print('Prompt: Multiple valid simfiles found:')
        found_simfiles: list[Simfile] = []
        found_simfile_paths: list[str] = []
        for sm_dir in sm_dirs:
            try:
                found_simfiles.append(simfile.opendir(sm_dir, strict=False)[0])
                found_simfile_paths.append(sm_dir)
            except Exception as e:
                print(f'Error reading simfile in {sm_dir}: {e}')
                continue
        print_simfile_choices(found_simfiles)
        total = len(found_simfiles)
        while True:
            print(f'Please choose a simfile to add [1-{total}]: ', end='')
            choice = input()
            if choice.isdigit() and int(choice) < total+1 and int(choice) > 0:
                # print(sm_dirs)
                print(f'Chosen dir: {sm_dirs[int(choice) - 1]}')
                root = found_simfile_paths[int(choice) - 1]
                break
            else:
                print('Invalid choice. Please choose again.')

    print('Song found at', root)
    print('Moving song to singles folder...')

    if config_data['delete-macos-files']:  # delete macos files if enabled
        delete_macos_files(root)

    # rename folder to zip name if no containing folder
    if root == TEMP:
        # TODO: Test if this works. Is importing from archive the only way this can happen?
        # What about other archive formats? (rar, 7z, etc.)
        # TODO: Consider using sm file name instead? Or sm.title?
        zip_name = os.path.basename(path).replace('.zip', '')
        shutil.move(root, root.replace(TEMP, zip_name))
        root = root.replace(TEMP, zip_name)

    # check if song folder already exists in singles folder
    dest = os.path.join(SINGLES, os.path.basename(root))
    if os.path.exists(dest):
        # TODO: output a diff of simfile metadata
        if config_data['delete-macos-files']:  # delete macos files if enabled
            delete_macos_files(dest)
        sm_new = simfile.opendir(root, strict=False)[0]
        sm_old = simfile.opendir(dest, strict=False)[0]
        print('Simfile dectected at destination.')
        print_simfile_data(sm_new, "New Simfile")
        print_simfile_data(sm_old, "Old Simfile")
        while True:
            print('Prompt: A folder with the same name already exists.')
            print(
                'Do you want to keep the [E]xisting simfile, or [O]verwrite? ', end='')
            choice = input().lower()
            if choice == 'e':
                print('Keeping old simfile. Exiting.\n')
                cleanup(TEMP)
                exit(0)
            elif choice == 'o':
                print('Overwriting old simfile.\n')
                shutil.rmtree(dest)
                break
            else:
                print('Invalid choice. Please choose again.')

    # Move the song to the singles folder
    shutil.move(root, dest)
    sm: Simfile = simfile.opendir(dest, strict=False)[0]
    print_simfile_data(sm, "Song added successfully")
    cleanup(TEMP)
