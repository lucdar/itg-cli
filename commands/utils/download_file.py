import gdown
import os
import pyrfc6266
import requests
from pathlib import Path
from tqdm import tqdm


def download_file(url: str, downloads: Path) -> Path:
    """
    Downloads a file from a URL to the downloads folder and returns a path to the downloaded file.
    Processes Google drive links using gdown and attempts to download other files using requests.
    Prints a progress bar to stderr.
    """
    # TODO: handle mega.nz links
    if "drive.google.com" in url or "drive.usercontent.google.com" in url:
        print("Making request to Google Drive...")
        download_path = gdown.download(
            url,
            quiet=False,
            fuzzy=True,
            output=os.path.join(downloads, ""),  # Append trailing /
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


def validate_response(r: requests.Response) -> None:
    """
    Validates a request response.
    Raises an exception if the status code is not 200, if the request does not have
    a content header, or if the Content-Type is not in valid_content_types
    """
    # TODO: add support for more filetypes (remember to update get_download_filename)
    valid_content_types = ["application/zip"]
    if r.status_code != 200:  # 200: OK
        raise Exception(f"Unsuccessful request to {r.url} with status {r.status_code}")
    if "Content-Type" not in r.headers:
        raise Exception("No Content-Type header found")
    if r.headers["Content-Type"] not in valid_content_types:
        raise Exception("Invalid Content-Type:", r.headers["Content-Type"])


def get_download_filename(r: requests.Response) -> str:
    """
    Returns the filename from the response's Content-Disposition header, the url's
    basename, or defaults to "download.zip"
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
    Writes the content from a streamed request `r` to `dest` and writes a progress bar to stderr
    """
    # https://stackoverflow.com/a/37573701/22049792
    chunk_size = 1024
    total_size = int(r.headers.get("content-length", 0))
    pbar = tqdm(total=total_size, unit="B", unit_scale=True, desc=dest.name)
    with open(dest, "wb") as file:
        for chunk in r.iter_content(chunk_size):
            pbar.update(len(chunk))
            file.write(chunk)
    pbar.close()
