import shutil
from pathlib import Path

import pytest
from conftest import make_pack, make_song
from itg_cli import (
    OverwriteException,
    UncensorException,
    add_pack,
    add_song,
    censor,
    get_censored,
    uncensor,
)


## add_pack ##
def test_add_pack_from_dir(library):
    src_pack = make_pack(library["src"], "Test Pack", ["Song A", "Song B"])
    pack, num_courses = add_pack(
        str(src_pack), library["packs"], library["courses"]
    )
    dest = library["packs"] / "Test Pack"
    assert dest.is_dir()
    assert (dest / "Song A" / "Song A.sm").is_file()
    assert len(list(pack.simfiles(strict=False))) == 2
    assert num_courses == 0
    # Local source is copied, not moved
    assert src_pack.is_dir()


def test_add_pack_from_zip(library):
    src_pack = make_pack(library["src"], "Zipped Pack", ["Song A"])
    zip_base = library["src"] / "archive" / "Zipped Pack"
    zip_base.parent.mkdir()
    zip_path = shutil.make_archive(
        zip_base, "zip", src_pack.parent, "Zipped Pack"
    )
    add_pack(zip_path, library["packs"], library["courses"])
    assert (library["packs"] / "Zipped Pack" / "Song A" / "Song A.sm").is_file()


def test_add_pack_with_courses(library):
    src_pack = make_pack(library["src"], "Course Pack", ["Song A"])
    courses_dir = src_pack / "Courses"
    courses_dir.mkdir()
    (courses_dir / "marathon.crs").write_text("#COURSE:Test Marathon;")
    _, num_courses = add_pack(
        str(src_pack), library["packs"], library["courses"]
    )
    assert num_courses == 1
    assert (library["courses"] / "Course Pack" / "marathon.crs").is_file()


def test_add_pack_no_courses_subfolder_when_pack_has_none(library):
    src_pack = make_pack(library["src"], "Plain Pack", ["Song A"])
    add_pack(str(src_pack), library["packs"], library["courses"])
    assert not (library["courses"] / "Plain Pack").exists()


def test_add_pack_empty_raises(library):
    empty = library["src"] / "Empty Pack"
    empty.mkdir()
    with pytest.raises(Exception, match="No packs found"):
        add_pack(str(empty), library["packs"], library["courses"])


def test_add_pack_overwrite_declined(library):
    src_pack = make_pack(library["src"], "Dupe Pack", ["Song A", "Song B"])
    add_pack(str(src_pack), library["packs"], library["courses"])
    with pytest.raises(OverwriteException):
        add_pack(str(src_pack), library["packs"], library["courses"])
    # Existing pack is untouched
    assert (library["packs"] / "Dupe Pack" / "Song A").is_dir()


def test_add_pack_overwrite_accepted(library):
    old_pack = make_pack(library["src"], "Dupe Pack", ["Old Song"])
    add_pack(str(old_pack), library["packs"], library["courses"])
    shutil.rmtree(old_pack)
    new_pack = make_pack(library["src"], "Dupe Pack", ["New Song"])
    add_pack(
        str(new_pack),
        library["packs"],
        library["courses"],
        overwrite=lambda _new, _old: True,
    )
    dest = library["packs"] / "Dupe Pack"
    assert (dest / "New Song").is_dir()
    assert not (dest / "Old Song").exists()


## add_song ##
def test_add_song_from_dir(library):
    src_song = make_song(library["src"], "Solo Song")
    singles = library["packs"] / "Singles"  # does not exist yet
    sf, loc = add_song(str(src_song), singles)
    assert (singles / "Solo Song" / "Solo Song.sm").is_file()
    assert sf.title == "Solo Song"
    assert Path(loc).is_file()
    # Local source is copied, not moved
    assert src_song.is_dir()


def test_add_song_multiple_raises(library):
    src_pack = make_pack(library["src"], "Two Songs", ["Song A", "Song B"])
    with pytest.raises(Exception, match="More than one simfile"):
        add_song(str(src_pack), library["packs"] / "Singles")


def test_add_song_overwrite_declined(library):
    src_song = make_song(library["src"], "Dupe Song")
    singles = library["packs"] / "Singles"
    add_song(str(src_song), singles)
    with pytest.raises(OverwriteException):
        add_song(str(src_song), singles)


def test_add_song_overwrite_accepted_clears_cache(library):
    src_song = make_song(library["src"], "Dupe Song")
    singles = library["packs"] / "Singles"
    add_song(str(src_song), singles)
    cache_entry = library["cache"] / "Songs" / "Songs_Singles_Dupe Song"
    cache_entry.write_text("stale cache data")
    add_song(
        str(src_song),
        singles,
        cache=library["cache"],
        overwrite=lambda _new, _old: True,
    )
    assert (singles / "Dupe Song" / "Dupe Song.sm").is_file()
    assert not cache_entry.exists()


def test_add_song_deletes_macos_files_at_dest(library):
    """Regression test: ._ files must be deleted from the *destination*."""
    src_song = make_song(library["src"], "Mac Song")
    (src_song / "._Mac Song.sm").write_bytes(b"\x00\x05\x16\x07")
    singles = library["packs"] / "Singles"
    add_song(str(src_song), singles, delete_macos_files_flag=True)
    assert (singles / "Mac Song" / "Mac Song.sm").is_file()
    assert not (singles / "Mac Song" / "._Mac Song.sm").exists()


## censor / uncensor ##
def test_censor_creates_censored_dir(library):
    """Regression test: censor must work when .censored does not exist yet."""
    src_pack = make_pack(library["src"], "Pack", ["Bad Song"])
    add_pack(str(src_pack), library["packs"], library["courses"])
    song_path = library["packs"] / "Pack" / "Bad Song"
    sm = censor(song_path, library["packs"], library["cache"])
    assert sm.title == "Bad Song"
    assert not song_path.exists()
    assert (library["packs"] / ".censored" / "Pack" / "Bad Song").is_dir()


def test_censor_outside_packs_raises(library):
    stray_song = make_song(library["src"], "Stray Song")
    with pytest.raises(Exception, match="is not a pack in"):
        censor(stray_song, library["packs"], library["cache"])


def test_censor_missing_path_raises(library):
    with pytest.raises(FileNotFoundError):
        censor(
            library["packs"] / "Pack" / "Ghost Song",
            library["packs"],
            library["cache"],
        )


def test_get_censored_empty(library):
    assert get_censored(library["packs"]) == []


def test_uncensor_no_censored_raises(library):
    """Regression test: must raise UncensorException, not FileNotFoundError."""
    with pytest.raises(UncensorException):
        uncensor(library["packs"])


def test_censor_uncensor_roundtrip(library):
    src_pack = make_pack(library["src"], "Pack", ["Bad Song"])
    add_pack(str(src_pack), library["packs"], library["courses"])
    song_path = library["packs"] / "Pack" / "Bad Song"
    censor(song_path, library["packs"], library["cache"])
    assert not song_path.exists()

    censored = get_censored(library["packs"])
    assert len(censored) == 1
    sm = uncensor(library["packs"], picker=lambda songs: 0)
    assert sm.title == "Bad Song"
    assert song_path.is_dir()
