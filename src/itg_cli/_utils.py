import gdown
import os
import pyrfc6266
import requests
import shutil
from itertools import chain
from pathlib import Path
from simfile.types import Simfile, Chart
from tqdm import tqdm
from typing import Iterable, Optional
from rich.prompt import Confirm


def simfile_paths(path: Path) -> Iterable[Path]:
    """
    Returns an iterator of valid paths to .sm or .ssc files that start with
    `path`. Paths that contain __MACOSX folders or whose simfiles begin with
    `.` are filtered.
    """

    def path_filter(p: Path):
        return not ("__MACOSX" in p.parts or p.name.startswith("."))

    sms = path.rglob("*.sm")
    sscs = path.rglob("*.ssc")
    return filter(path_filter, chain(sms, sscs))


def get_charts_string(sm: Simfile, difficulty_labels: bool = False) -> str:
    """
    Returns the string representation of chart meters of a simfile (with
    quotes removed). Also includes the difficulty label if `difficulty_labels`
    is True.

    Example:
        `get_charts_string(sm)`
        returns: `"[5, 7, 10, 12]"`
        `get_charts_string(sm, difficulty_labels=True)`
        returns: `"[Easy 5, Medium 7, Hard 10, Challenge 12]"`
    """

    def fn(c: Chart):
        if difficulty_labels:
            return f"{c.difficulty} {c.meter}"
        else:
            return c.meter

    return str([fn(c) for c in sm.charts]).replace("'", "")


def delete_macos_files(path: Path) -> None:
    """Deletes all `._` files in the supplied path"""
    list(map(Path.unlink, path.rglob("._*")))


def extract(archive_path: Path) -> Path:
    """
    Extracts an archive to a containing folder in the same directory.
    Returns the path to the containing folder.

    Uses shutil.unpack_archive, and thus only supports the following
    formats:
    `zip, tar, gztar, bztar, xztar`
    """
    dest = archive_path.with_suffix("")
    dest.mkdir()
    print("Extracting archive...")
    shutil.unpack_archive(archive_path, dest)
    return dest


def prompt_overwrite(item: str) -> bool:
    """
    Prompts the user to overwrite the existing `item`.
    Overwriting returns `True`, Keeping returns `False`.
    """
    return Confirm.ask(f"Overwrite existing {item}?", default=True)


def setup_working_dir(
    path_or_url: str, temp: Path, downloads: Optional[Path]
) -> Path:
    """
    Takes the supplied parameter for an add command and does any necessary
    extraction/downloading. Moves the directory to temp if it was downloaded
    or extracted; copies if supplied as a path to a local directory instead.
    If downloads is None, saves the downloaded file to the temp dir so it is
    deleted when the program exits.
    """
    downloaded, extracted = False, False
    # Download if URL
    if path_or_url.startswith("http"):
        if downloads is None:
            path = download_file(path_or_url, temp)
        else:
            path = download_file(path_or_url, downloads)
        downloaded = True
    else:
        path = Path(path_or_url).absolute()
    if not path.exists():
        raise FileNotFoundError("File does not exist:", str(path))
    if not path.is_dir():
        path = extract(path)
        extracted = True
    working_path = temp.joinpath(path.name)
    if downloaded or extracted:
        shutil.move(path, working_path)
    else:
        shutil.copytree(path, working_path)
    return working_path


def download_file(url: str, downloads: Path) -> Path:
    """
    Downloads a file from a URL to the downloads folder and returns a path to
    the downloaded file. Processes Google drive links using gdown and attempts
    to download other files using requests. Prints a progress bar to stderr.
    """
    # TODO: handle mega.nz links
    if "drive.google.com" in url or "drive.usercontent.google.com" in url:
        print("Making request to Google Drive...")
        download_path = gdown.download(
            url,
            quiet=False,
            fuzzy=True,
            output=os.path.join(downloads, ""),  # Append trailing `/`
        )
        return Path(download_path)
    else:  # try using requests
        print(f"Making request to {url}...")
        response = requests.get(url, allow_redirects=True, stream=True)
        validate_response(response)
        filename = get_download_filename(response)
        dest = downloads.joinpath(filename)
        # Delete dest if it exists
        dest.unlink(missing_ok=True)
        download_with_progress(response, dest)
        return dest


def validate_response(
    r: requests.Response, valid_content_types: list[str] = ["application/zip"]
) -> None:
    """
    Validates a request response.

    Raises an exception if the status code is not 200, if the request does not
    have a content header, or if the Content-Type is not in
    `valid_content_types`
    """
    # TODO: add support for more filetypes (and update get_download_filename)
    if r.status_code != 200:  # 200: OK
        raise Exception(
            f"Unsuccessful request to {r.url} with status {r.status_code}"
        )
    if "Content-Type" not in r.headers:
        raise Exception("No Content-Type header found")
    if r.headers["Content-Type"] not in valid_content_types:
        raise Exception("Invalid Content-Type:", r.headers["Content-Type"])


def get_download_filename(r: requests.Response) -> str:
    """
    Returns the filename from the response's Content-Disposition header, the
    url's basename, or defaults to "download.zip"
    """
    if "Content-Disposition" in r.headers:
        return Path(pyrfc6266.parse_filename(r.headers["Content-Disposition"]))
    name = os.path.basename(r.url)
    if name.endswith(".zip"):
        return name
    else:
        return "download.zip"


def download_with_progress(r: requests.Response, dest: Path) -> None:
    """
    Downloads the content from a streamed request `r` to a .part file. Writes a
    progress bar to stderr tracking progress. Moves the file to dest once it is
    finished downloading.
    """
    # Write the file with a munged extension before it's fully downloaded
    munged_dest = dest.with_suffix(dest.suffix + ".part")
    # https://stackoverflow.com/a/37573701/22049792
    chunk_size = 1024
    total_size = int(r.headers.get("content-length", 0))
    pbar = tqdm(total=total_size, unit="B", unit_scale=True, desc=dest.name)
    with open(munged_dest, "wb") as file:
        for chunk in r.iter_content(chunk_size):
            pbar.update(len(chunk))
            file.write(chunk)
    shutil.move(munged_dest, dest)
    pbar.close()
