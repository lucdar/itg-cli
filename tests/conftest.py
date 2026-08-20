from pathlib import Path

import pytest

SM_TEMPLATE = """#TITLE:{title};
#ARTIST:Test Artist;
#OFFSET:0.000;
#BPMS:0.000=120.000;
#NOTES:
     dance-single:
     :
     Beginner:
     1:
     0.000,0.000,0.000,0.000,0.000:
0000
0000
0000
0000
;
"""


def make_song(parent: Path, name: str, title: str | None = None) -> Path:
    """Creates a song folder containing a minimal .sm file. Returns its path."""
    song_dir = parent / name
    song_dir.mkdir(parents=True)
    sm_path = song_dir / f"{name}.sm"
    sm_path.write_text(SM_TEMPLATE.format(title=title or name))
    return song_dir


def make_pack(parent: Path, name: str, song_names: list[str]) -> Path:
    """Creates a pack folder containing the given songs. Returns its path."""
    pack_dir = parent / name
    pack_dir.mkdir(parents=True)
    for song_name in song_names:
        make_song(pack_dir, song_name)
    return pack_dir


@pytest.fixture
def library(tmp_path: Path) -> dict[str, Path]:
    """An itgmania-like directory layout with packs, courses, and cache."""
    dirs = {
        "packs": tmp_path / "Songs",
        "courses": tmp_path / "Courses",
        "cache": tmp_path / "Cache",
        "src": tmp_path / "src",  # holds input packs/songs for tests
    }
    for d in dirs.values():
        d.mkdir()
    (dirs["cache"] / "Songs").mkdir()
    return dirs
