import requests
import gdown
import os
import pyrfc6266
import tqdm
from pathlib import Path


def download_file(url: str, downloads: Path) -> Path:
    """
    Downloads a file from a URL to the downloads folder and returns a path to the downloaded file.
    Processes Google drive links using gdown and attempts to download other files using requests.
    Prints a progress bar to stderr.
    """
    # TODO: handle mega.nz links
    if "drive.google.com" in url or "drive.usercontent.google.com" in url:
        download_path = gdown.download(
            url,
            quiet=False,
            fuzzy=True,
            output=os.path.join(downloads, ""),  # Append trailing /
        )
        return Path(download_path)
    else:  # try using requests
        response = requests.get(url, allow_redirects=True)
        validate_response(response)
        filename = get_download_filename(response)
        dest = downloads.joinpath(filename)
        if dest.exists():
            os.remove(dest)
        download_with_progress(response, filename, dest)
        return dest


def validate_response(r: requests.Response) -> None:
    """
    Validates a request response.
    Raises an exception if the status code is not 200, if the request does not have
    a content header, or if the Content-Type is not in valid_content_types
    """
    # TODO: add support for more filetypes (need to change get_download_filename)
    valid_content_types = ["application/zip"]
    if r.status_code != 200:  # 200: OK
        raise Exception(f"Unsuccessful request to {r.url} with status {r.status_code}")
    if "Content-Type" not in r.headers:
        raise Exception("No Content-Type header found")
    if r.headers["Content-Type"] not in valid_content_types:
        raise Exception("Invalid Content-Type:", r.headers["Content-Type"])


def get_download_filename(r: requests.Response) -> Path:
    """
    Returns the filename from the response's Content-Disposition header, the url's
    basename, or defaults to "download.zip"
    """
    if "Content-Disposition" in r.headers:
        return Path(pyrfc6266.parse_filename(r.headers["Content-Disposition"]))
    name = os.path.basename(r.url)
    if name != "":
        return Path(name).with_suffix(".zip")
    else:
        return Path("download.zip")


def download_with_progress(r: requests.Response, dest: Path) -> None:
    """
    Writes the content from a request r to dest
    Displays a progress bar in stdout.
    """
    chunk_size = 128
    total_size = r.headers.get("content-length", None)
    if total_size is not None:
        total_size = int(total_size)
    pbar = tqdm.tqdm(total=total_size, unit="B", unit_scale=True, desc=dest.name)
    with open(dest, "wb") as file:
        for chunk in r.iter_content(chunk_size=chunk_size):
            file.write(chunk)
            pbar.update(len(chunk))
    pbar.close()
