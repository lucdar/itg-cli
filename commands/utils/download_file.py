import requests
import gdown
import shutil
import os
import pyrfc6266
import tqdm
from tempfile import TemporaryDirectory
from config import settings
from .add_utils import prompt_overwrite

DOWNLOADS = settings.downloads


def download_file(url):
    """
    Downloads a file from a URL to the downloads folder and returns a path to the downloaded file.
    If the file already exists, prompts the user to overwrite it or use the existing file.
    Processes Google drive links using gdown and attempts to download other files using requests.
    Prints a progress bar to stderr.
    """
    # create DOWNLOADS folder if it doesn't exist
    if os.path.exists(DOWNLOADS) is False:
        os.mkdir(DOWNLOADS)

    if url.startswith("http") is False:
        print("Invalid URL:", url)
        exit(1)

    # if 'mega.nz' in url or 'mega.co.nz' in url:
    #     # Detect installation of megacmd
    #     if shutil.which('megacmd') is None:
    #         raise Exception('Error: megacmd not installed')
    if "drive.google.com" in url or "drive.usercontent.google.com" in url:
        # TODO: look into removing temporary directory and move
        with TemporaryDirectory() as tempdir:
            loc = gdown.download(
                url, quiet=False, fuzzy=True, output=os.path.join(tempdir, "")
            )
            filename = os.path.basename(loc)
            dest = os.path.join(DOWNLOADS, filename)
            if os.path.exists(dest):
                os.remove(dest)
            shutil.move(loc, dest)
            return dest
    else:  # try using requests
        r = requests.get(url, allow_redirects=True)
        if r.status_code != 200:
            print(f"Error downloading file from {url}")
            print("Status code:", r.status_code)
            exit(1)
        if "Content-Type" not in r.headers.keys():
            print("No Content-Type header found")
            exit(1)
        elif r.headers["Content-Type"] == "application/zip":
            if "Content-Disposition" not in r.headers.keys():
                filename = os.path.basename(url) + ".zip"
            else:
                # parse filename from Content-Disposition header
                # Apparently this is nontrivial so the pyrfc6266 library is used
                filename = pyrfc6266.parse_filename(r.headers["Content-Disposition"])
            dest = os.path.join(DOWNLOADS, filename)
            if os.path.exists(dest):
                if prompt_overwrite("downloaded file") is False:
                    return dest
                else:
                    os.remove(dest)
            chunk_size = 128
            total_size = r.headers.get("content-length", None)
            if total_size is not None:
                total_size = int(total_size)
            pbar = tqdm.tqdm(total=total_size, unit="B", unit_scale=True, desc=filename)
            with open(dest, "wb") as file:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    pbar.update(len(chunk))
            pbar.close()
            return dest
        else:
            print("Invalid Content-Type:", r.headers["Content-Type"])
            exit(1)
