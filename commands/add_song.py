import zipfile
import os
import shutil
import simfile

TEMP = '.temp'
SONGS = 'songs/singles'


def cleanup():  # Remove the temp directory if it exists
    if os.path.exists(TEMP):
        shutil.rmtree(TEMP)


def printSimfileData(sm: simfile.types.Simfile, label: str):
    print(f"### {label} ###")
    print("  Title: " + sm.title,
          " Artist: " + sm.artist,
          " Credit: " + sm.credit,
          " Meters: " + str(list(map((lambda c: c.meter), sm.charts))),
          sep='\n')
    print()


def add_song(args):
    # clear temp directory if not empty
    cleanup()

    # TODO: add support for downloading from URLs using requests
    if args.path.startswith('http'):
        # path = download_file(args.path)
        print('URLs are not supported yet')
        raise NotImplementedError
    else:
        path = args.path

    # validate path
    if path is None:
        print('no path supplied')
        exit(1)
    if os.path.exists(path) is False:
        print('invalid path or URL:', path)
        exit(1)
    if path.endswith('.zip'):  # extract song if zip file
        with zipfile.ZipFile(args.path, 'r') as zip_ref:
            zip_ref.extractall(TEMP)
    if os.path.isdir(path):  # copy song if directory
        shutil.copytree(path, TEMP)

    # dectect valid simfile directory
    valid_dirs = []
    for root, _, files in os.walk(TEMP):
        if "__MACOSX" in root:  # ignore macosx folders
            continue
        for file in files:
            if file.endswith('.sm') or file.endswith('.ssc'):
                valid_dirs.append(root)
                break
    if len(valid_dirs) == 0:
        print('no valid simfile found')
        cleanup()
        exit(1)
    if len(valid_dirs) > 1:
        # TODO: ask user which simfile(s) to add if multiple are found.
        print('Multiple valid simfiles found.',
              'Please only include one simfile in the zip file.')
        cleanup()
        raise NotImplementedError

    root = valid_dirs[0]

    # rename folder to zip name if no containing folder
    if root == TEMP:
        # TODO: make this OS agnostic
        zip_name = args.path.split('/')[-1].split('.')[0]
        shutil.move(root, root.replace(TEMP, zip_name))
        root = root.replace(TEMP, zip_name)

    # check if song already exists
    dest = os.path.join(SONGS, root.split('/')[-1])
    if os.path.exists(dest):
        # TODO: output a diff of simfile metadata
        sm_new = simfile.opendir(root, strict=False)[0]
        sm_old = simfile.opendir(dest, strict=False)[0]
        print('Simfile dectected at destination.')
        printSimfileData(sm_new, "New Simfile")
        printSimfileData(sm_old, "Old Simfile")
        while True:
            print('Do you want to keep or overwrite the old simfile?')
            print('  [K]eep or [O]verwrite: ', end='')
            choice = input().upper()
            if choice == 'K':
                print('Keeping old simfile. Exiting.\n')
                cleanup()
                exit(0)
            if choice == 'O':
                print('Overwriting old simfile.\n')
                shutil.rmtree(dest)
                break
            else:
                print('Invalid choice. Please choose again.')

    # Move the song to the singles folder
    shutil.move(root, dest)
    sm: simfile.types.Simfile = simfile.opendir(dest, strict=False)[0]
    printSimfileData(sm, "Song added successfully")
    cleanup()
    exit(0)
