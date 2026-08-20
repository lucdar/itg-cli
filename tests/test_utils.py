import shutil
from types import SimpleNamespace

import pytest
from conftest import make_pack
from itg_cli._utils import (
    delete_macos_files,
    extract,
    get_download_filename,
    simfile_paths,
    validate_response,
)


## simfile_paths ##
def test_simfile_paths_finds_sm_and_ssc(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "a.sm").touch()
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "b.ssc").touch()
    found = {p.name for p in simfile_paths(tmp_path)}
    assert found == {"a.sm", "b.ssc"}


def test_simfile_paths_filters_macosx_and_hidden(tmp_path):
    (tmp_path / "__MACOSX" / "a").mkdir(parents=True)
    (tmp_path / "__MACOSX" / "a" / "a.sm").touch()
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "._b.sm").touch()
    (tmp_path / "b" / "b.sm").touch()
    found = {p.name for p in simfile_paths(tmp_path)}
    assert found == {"b.sm"}


## delete_macos_files ##
def test_delete_macos_files(tmp_path):
    (tmp_path / "song").mkdir()
    (tmp_path / "song" / "._song.sm").touch()
    (tmp_path / "song" / "song.sm").touch()
    delete_macos_files(tmp_path)
    assert not (tmp_path / "song" / "._song.sm").exists()
    assert (tmp_path / "song" / "song.sm").exists()


## extract ##
def test_extract_zip(tmp_path):
    pack = make_pack(tmp_path / "input", "Pack", ["Song A"])
    zip_path = shutil.make_archive(
        tmp_path / "Pack", "zip", pack.parent, "Pack"
    )
    dest = extract(pack.parent.parent / "Pack.zip")
    assert dest == tmp_path / "Pack"
    assert (dest / "Pack" / "Song A" / "Song A.sm").is_file()
    assert zip_path  # silence unused warning


def test_extract_targz(tmp_path):
    pack = make_pack(tmp_path / "input", "Pack", ["Song A"])
    shutil.make_archive(tmp_path / "Pack", "gztar", pack.parent, "Pack")
    dest = extract(tmp_path / "Pack.tar.gz")
    assert (dest / "Pack" / "Song A" / "Song A.sm").is_file()


def test_extract_invalid_suffix_raises(tmp_path):
    bogus = tmp_path / "pack.rar"
    bogus.touch()
    # Message must interpolate the actual suffix (f-string regression test)
    with pytest.raises(ValueError, match=r"\.rar"):
        extract(bogus)


## validate_response ##
def make_response(content_type="application/zip", status=200):
    return SimpleNamespace(
        status_code=status,
        headers={"Content-Type": content_type},
        url="https://example.com/pack.zip",
    )


def test_validate_response_ok():
    validate_response(make_response())


def test_validate_response_content_type_with_params():
    validate_response(make_response("application/zip; charset=binary"))


def test_validate_response_octet_stream():
    validate_response(make_response("application/octet-stream"))


def test_validate_response_html_raises():
    with pytest.raises(Exception, match="Invalid Content-Type"):
        validate_response(make_response("text/html"))


def test_validate_response_bad_status_raises():
    with pytest.raises(Exception, match="status 404"):
        validate_response(make_response(status=404))


## get_download_filename ##
def test_filename_from_content_disposition():
    r = SimpleNamespace(
        headers={"Content-Disposition": 'attachment; filename="pack.zip"'},
        url="https://example.com/download",
    )
    assert get_download_filename(r) == "pack.zip"


def test_filename_contains_no_path_separators():
    r = SimpleNamespace(
        headers={
            "Content-Disposition": 'attachment; filename="../../evil.zip"'
        },
        url="https://example.com/download",
    )
    name = get_download_filename(r)
    assert "/" not in name and "\\" not in name
    assert name.endswith("evil.zip")


def test_filename_from_url():
    r = SimpleNamespace(headers={}, url="https://example.com/pack.zip")
    assert get_download_filename(r) == "pack.zip"


def test_filename_fallback():
    r = SimpleNamespace(headers={}, url="https://example.com/download?id=42")
    assert get_download_filename(r) == "download.zip"
