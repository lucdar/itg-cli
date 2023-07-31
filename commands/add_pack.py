import os
import shutil
from simfile.dir import SimfilePack
from .utils.download_file import download_file
from .utils.add_utils import cleanup, extract_archive, find_simfile_dirs, get_charts_string
from config import config_data

TEMP_ROOT = config_data['temp_root']
PACKS = config_data['packs']
COURSES = config_data['courses']


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
        cleanup(TEMP)
        raise NotImplementedError('Multiple valid pack directories found')

    try:
        pack = SimfilePack(pack_dirs[0])
    except Exception as e:
        # if DuplicateSimfileError, then uhhh idk
        if e.__class__.__name__ == 'DuplicateSimfileError':
            raise NotImplementedError(
                'A song with multiple .sm or .ssc files has been detected. This is not supported yet.')
    songs = list(pack.simfiles())

    # print pack metadata
    print("Pack metadata:")
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
            print('Prompt: Pack already exists (with the same number of songs).')
        elif difference > 0:
            print(
                f"Prompt: Pack already exists with {difference} fewer songs.")
        else:  # difference < 0
            print(
                f"Prompt: Pack already exists with {abs(difference)} more songs.")
        while True:
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

    # look for a Courses folder containing files with .crs extension
    print('Searching for courses...', end='')
    added_courses = False
    crs_dirs: list[str] = []
    for root, _, files in os.walk(TEMP):
        for file in files:
            if file.endswith('.crs') and 'Courses' in root:
                crs_dirs.append(os.path.join(root, file))
    if len(crs_dirs) > 0:
        print(f"\rFound {len(crs_dirs)} courses:".ljust(24, ' '))
        for crs in crs_dirs:
            print(f"  {os.path.basename(crs)}")
        while True:
            print('Prompt: Do you want to add these courses? [Y/n] ', end='')
            choice = input().lower()
            if choice == 'y':
                # copy all files in directories with .crs files to courses subfolder
                # important to copy all files because banners are not .crs files
                courses_subfolder = os.path.join(COURSES, pack.name)
                if os.path.exists(courses_subfolder):
                    shutil.rmtree(courses_subfolder)
                os.mkdir(courses_subfolder)
                courses_dirs = [os.path.dirname(crs) for crs in crs_dirs]
                courses_dirs_set = set(courses_dirs)
                for courses_dir in courses_dirs_set:
                    for file in os.listdir(courses_dir):
                        file_dir = os.path.join(courses_dir, file)
                        if os.path.isfile(file_dir):
                            shutil.copy(file_dir, courses_subfolder)
                added_courses = True
                break
            elif choice == 'n':
                break
            else:
                print('Invalid choice')
    else:
        print('\rNo courses found.'.ljust(24, ' '))

    # move pack to packs directory
    shutil.move(pack.pack_dir, os.path.join(PACKS, pack.name))
    print(
        f"Added pack {'and courses' if added_courses else ''} successfully!")
    cleanup(TEMP)
