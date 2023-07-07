import json
import os
import shutil
import simfile
from simfile.types import Simfile
from .utils.download_file import download_file
from .utils.get_charts import getChartsAsStrings

TEMP = '.temp/'
SINGLES = 'songs/singles'


def cleanup():  # Remove the temp directory if it exists
    if os.path.exists(TEMP):
        shutil.rmtree(TEMP)


def printSimfileData(sm: Simfile, label: str = 'data'):
    print(f"### {label} ###",
          "  Title: " + sm.title,
          " Artist: " + sm.artist,
          " Meters: " + str(getChartsAsStrings(sm)),
          sep='\n', end='\n\n')


def printSimfileChoices(simfiles: list[Simfile], jsonOutput=False) -> None:
    total = len(simfiles)
    if jsonOutput:
        simfileDict = []
        for i, sm in enumerate(simfiles):
            simfile = {
                "index": i+1,
                "title": sm.title,
                "artist": sm.artist,
                "charts": getChartsAsStrings(sm, difficulty_labels=True)
            }
            simfileDict.append(simfile)
        print(json.dumps(simfileDict, indent=4))
    else:
        for i, sm in enumerate(simfiles):
            # format chart list output
            charts = getChartsAsStrings(sm, difficulty_labels=True)
            charts = str(charts).replace("'", "")
            indent = len(str(total)) - len(str(i+1))
            chartIndent = len(str(total)) + 3
            print(' ' * indent + f'[{i+1}] {sm.title} - {sm.artist}',
                  ' ' * chartIndent + f'{charts}',
                  sep='\n')


def add_song(args):
    # clear temp directory if not empty
    cleanup()

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
    else:
        # Attempt to extract archive
        os.mkdir(TEMP)
        try:
            shutil.unpack_archive(path, TEMP)
        except:
            cleanup()
            raise Exception('Error extracting archive')

    # dectect valid simfile directory
    print('Searching for valid simfiles...')
    valid_dirs = []
    for root, _, files in os.walk(TEMP):
        if "__MACOSX" in root:  # ignore macosx folders
            continue
        for file in files:
            if file.startswith('.'):  # ignore hidden files
                continue
            if file.endswith('.sm') or file.endswith('.ssc'):
                valid_dirs.append(root)
                break
    if len(valid_dirs) == 0:
        cleanup()
        raise Exception('No valid simfiles found')
    if len(valid_dirs) > 1:
        print('Multiple valid simfiles found:')
        found_simfiles: list[Simfile] = []
        found_simfile_paths: list[str] = []
        for dir in valid_dirs:
            try:
                found_simfiles.append(simfile.opendir(dir, strict=False)[0])
                found_simfile_paths.append(dir)
            except Exception as e:
                print(f'Error reading simfile in {dir}: {e}')
                continue
        printSimfileChoices(found_simfiles)
        total = len(found_simfiles)
        while True:
            print(f'Please choose a simfile to add [1-{total}]: ', end='')
            choice = input()
            if choice.isdigit() and int(choice) < total+1 and int(choice) > 0:
                # print(valid_dirs)
                print(f'Chosen dir: {valid_dirs[int(choice) - 1]}')
                root = found_simfile_paths[int(choice) - 1]
                break
            else:
                print('Invalid choice. Please choose again.')
    else:
        root = valid_dirs[0]

    print('Song found at', root)
    print('Moving song to singles folder...')

    # rename folder to zip name if no containing folder
    if root == TEMP:
        # TODO: Test if this works
        zip_name = os.path.basename(path).replace('.zip', '')
        shutil.move(root, root.replace(TEMP, zip_name))
        root = root.replace(TEMP, zip_name)

    # check if song already exists
    dest = os.path.join(SINGLES, os.path.basename(root))
    if os.path.exists(dest):
        # TODO: output a diff of simfile metadata
        sm_new = simfile.opendir(root, strict=False)[0]
        sm_old = simfile.opendir(dest, strict=False)[0]
        print('Simfile dectected at destination.')
        printSimfileData(sm_new, "New Simfile")
        printSimfileData(sm_old, "Old Simfile")
        while True:
            print('Prompt: A folder with the same name already exists.')
            print(
                'Do you want to keep the [E]xisting simfile, or [O]verwrite? ', end='')
            choice = input().lower()
            if choice == 'e':
                print('Keeping old simfile. Exiting.\n')
                cleanup()
                exit(0)
            if choice == 'o':
                print('Overwriting old simfile.\n')
                shutil.rmtree(dest)
                break
            else:
                print('Invalid choice. Please choose again.')

    # Move the song to the singles folder
    shutil.move(root, dest)
    sm: Simfile = simfile.opendir(dest, strict=False)[0]
    printSimfileData(sm, "Song added successfully")
    cleanup()
