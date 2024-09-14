import simfile
import os
import shutil
import sys
from config import settings

CENSORED_PATH = settings.censored
SONGS_PATH = settings.packs
CACHE = settings.cache


def censor(args):
    path = os.path.abspath(args.path)
    if not os.path.exists(path):
        print(f"Error: {path} does not exist")
        sys.exit(1)

    # Check that the path is a simfile
    try:
        simfile.opendir(path, strict=False)
    except Exception as e:
        print(f"Error: {path} is not a valid simfile directory: {e}")
        sys.exit(1)

    # Move the simfile to the censored folder under the same pack subdirectory
    pack_and_song = os.path.relpath(path, start=SONGS_PATH)
    destination = os.path.join(CENSORED_PATH, pack_and_song)
    try:
        shutil.move(path, destination)
    except Exception as e:
        print(f"Error: Could not move {path} to {destination}: {e}")
        sys.exit(1)

    # Remove the song's cache entry if it exists
    if CACHE != "":
        packname, songname = os.path.split(pack_and_song)
        # Cache Files are named Songs_PackName_SongFolderName
        cache_entry = f"Songs_{packname}_{songname}"
        cache_entry_path = os.path.join(CACHE, "Songs", cache_entry)
        if os.path.exists(cache_entry_path):
            os.remove(cache_entry_path)
        else:
            print("Warning: Cache entry not found. Skipping.")


def uncensor():
    # List the files that are currently censored and build a list of choices
    song_path_fragments = []  # os.path.join(pack_folder, song_folder) list
    for pack in os.listdir(CENSORED_PATH):
        print(f"### {pack} ###")
        pack_path = os.path.join(CENSORED_PATH, pack)
        for song in os.listdir(pack_path):
            song_path_fragments.append(os.path.join(pack, song))
            print(f"[{len(song_path_fragments)}] {song}")
        print()

    print("Prompt: Please select a song to uncensor ", end="")
    while True:
        choice = input()
        i = int(choice)
        if choice.isdigit() and i < len(song_path_fragments) + 1 and i > 0:
            chosen_song = song_path_fragments[i - 1]
            print(f"Chosen song: {chosen_song}")
            song_path = os.path.join(CENSORED_PATH, chosen_song)
            destination = os.path.join(SONGS_PATH, os.path.dirname(chosen_song))
            try:
                shutil.move(song_path, destination)
            except Exception as e:
                print(f"Error: Could not move {song_path} to {destination}: {e}")
                sys.exit(1)
            break
        else:
            print("Invalid choice. Please choose again.")
