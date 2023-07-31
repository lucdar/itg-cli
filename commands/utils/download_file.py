import requests
import gdown
import shutil
import os
import pyrfc6266
import tqdm
from config import config_data

DOWNLOADS = config_data['downloads']
TMP_ROOT = config_data['temp_root']


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

    if url.startswith('http') is False:
        print('Invalid URL:', url)
        exit(1)

    # if 'mega.nz' in url or 'mega.co.nz' in url:
    #     # Detect installation of megacmd
    #     if shutil.which('megacmd') is None:
    #         raise Exception('Error: megacmd not installed')
    if 'drive.google.com' in url:
        os.chdir(TMP_ROOT)  # change cwd to temp folder
        filename = gdown.download(url, quiet=False, fuzzy=True)
        loc = os.path.join(os.getcwd(), filename)
        dest = os.path.join(DOWNLOADS, filename)
        # if file exists already prompt user to overwrite
        if os.path.exists(dest):
            if prompt_overwrite():
                os.remove(dest)
                shutil.move(loc, dest)
            else:
                os.remove(loc)
        else:
            shutil.move(loc, dest)
        return dest
    else:  # try using requests
        r = requests.get(url, allow_redirects=True)
        if r.status_code != 200:
            print(f'Error downloading file from {url}')
            print('Status code:', r.status_code)
            exit(1)
        if not 'Content-Type' in r.headers.keys():
            print('No Content-Type header found')
            exit(1)
        elif r.headers['Content-Type'] == 'application/zip':
            if 'Content-Disposition' not in r.headers.keys():
                filename = os.path.basename(url) + '.zip'
            else:
                # parse filename from Content-Disposition header
                # Apparently this is nontrivial so the pyrfc6266 library is used
                filename = pyrfc6266.parse_filename(
                    r.headers['Content-Disposition'])
            dest = os.path.join(DOWNLOADS, filename)
            if os.path.exists(dest):
                if prompt_overwrite() is False:
                    return dest
                else:
                    os.remove(dest)
            chunk_size = 128
            total_size = r.headers.get('content-length', None)
            if total_size is not None:
                total_size = int(total_size)
            pbar = tqdm.tqdm(total=total_size, unit="B",
                             unit_scale=True, desc=filename)
            with open(dest, 'wb') as file:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    pbar.update(len(chunk))
            pbar.close()
            return dest
        else:
            print('Invalid Content-Type:', r.headers['Content-Type'])
            exit(1)


def prompt_overwrite():
    """ 
    Prompts the user to overwrite a file if one exists with the same name.
    Returns True if the file should be overwritten, False if the old file should be used instead.
    """
    print('Prompt: Overwrite cached download file?')
    print('Use [E]xisting file or [O]verwrite?')
    while True:
        res = input()
        if res.lower() == 'e':
            return False
        elif res.lower() == 'o':
            return True
        else:
            print('Invalid input. Please enter E or O.')
