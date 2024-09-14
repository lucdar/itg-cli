import requests
import gdown
import os
import pyrfc6266
import tqdm
from config import settings

DOWNLOADS = settings.downloads


def download_file(url):
    """
    Downloads a file from a URL to the downloads folder and returns a path to the downloaded file.
    Processes Google drive links using gdown and attempts to download other files using requests.
    Prints a progress bar to stderr.
    """
    # TODO: handle mega.nz links
    if "drive.google.com" in url or "drive.usercontent.google.com" in url:
        return gdown.download(
            url, quiet=False, fuzzy=True, output=os.path.join(DOWNLOADS, "")
        )
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
