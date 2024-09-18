import shutil
from collections import Counter
from pathlib import Path
from simfile.dir import SimfilePack
from tempfile import TemporaryDirectory
from .utils.add_utils import (
    setup_working_dir,
    simfile_paths,
    delete_macos_files,
    get_charts_string,
    prompt_overwrite,
)


def add_pack(args, settings):
    with TemporaryDirectory() as temp_directory:
        working_dir = setup_working_dir(
            args.path, Path(settings.downloads), Path(temp_directory)
        )

        # 2nd parent of a simfile path is a valid pack directory
        # pack_dir_counts stores the # of simfiles in each pack
        pack_dir_counts = Counter(
            map(lambda p: p.parents[1], simfile_paths(working_dir))
        )
        if len(pack_dir_counts) == 0:
            raise Exception("No packs found.")
        elif len(pack_dir_counts) > 1:
            print("Warning | Multiple pack directories found:")
            packs_by_frequency = pack_dir_counts.most_common()
            for pack, count in packs_by_frequency:
                print(f"{pack.relative_to(working_dir)} ({count} songs)")
            pack_path = packs_by_frequency[0][0]
            print(
                f"Selecting pack with the most songs: {pack_path.relative_to(working_dir)}"
            )
        else:
            pack_path, _ = pack_dir_counts.popitem()

        if settings.delete_macos_files:
            delete_macos_files(pack_path)
        pack = SimfilePack(pack_path)
        songs = list(pack.simfiles(strict=False))

        # print pack metadata
        print(f"{pack.name} contains {len(songs)} songs:")
        for song in songs:
            print(f"  {get_charts_string(song)} {song.title} ({song.artist})")

        # check if pack already exists
        dest = Path(settings.packs).joinpath(pack_path.name)
        if dest.exists():
            if not args.overwrite:
                if settings.delete_macos_files:
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
                if not prompt_overwrite("pack"):
                    exit(1)
            shutil.rmtree(dest)

        # look for a Courses folder countaining .crs files
        num_courses = 0
        courses_subfolder = Path(settings.courses).joinpath(pack.name)
        courses_subfolder.mkdir(exist_ok=True)
        crs_parent_dirs = set(map(lambda p: p.parent, working_dir.rglob("*.crs")))
        for crs_parent_dir in crs_parent_dirs:
            for file in filter(Path.is_file, crs_parent_dir.iterdir()):
                file.replace(courses_subfolder.joinpath(file.name))
                if file.suffix == ".crs":
                    num_courses += 1
        # move pack to packs directory
        pack_path.rename(dest)

    # Print success message
    if num_courses == 1:
        print(f"Added {pack.name} with {len(songs)} songs and 1 course.")
    else:
        print(f"Added {pack.name} with {len(songs)} songs and {num_courses} courses.")
