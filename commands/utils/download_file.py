import requests
import gdown
# from mega import Mega
import shutil
import os
import pyrfc6266

DLS = '.dls/'


def download_file(url):
    """
    Downloads a file from a URL to the DLS folder and returns a path to the downloaded file.
    Processes Google drive links using gdown and attempts to download other files using requests
    """
    # create DLS folder if it doesn't exist
    if os.path.exists(DLS) is False:
        os.mkdir(DLS)

    if url.startswith('http') is False:
        print('Invalid URL:', url)
        exit(1)

    # Enumerate cases for different file hosts
    # if 'mega.nz' in url or 'mega.co.nz' in url:
    #     m = Mega()
    #     return m.download_url(url, DLS)
    if 'drive.google.com' in url:
        filename = gdown.download(url, quiet=False, fuzzy=True)
        loc = os.path.join(os.getcwd(), filename)
        dest = os.path.join(DLS, filename)
        # if file exists already prompt user to overwrite
        if os.path.exists(dest):
            if prompt_overwrite(dest):
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
                filename = pyrfc6266.parse_filename(
                    r.headers['Content-Disposition'])
            if prompt_overwrite(os.path.join(DLS, filename)) is False:
                return os.path.join(DLS, filename)
            chunk_size = 128
            total_size = int(r.headers.get('content-length', 0))
            with open(os.path.join(DLS, filename), 'wb') as file:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    downloaded_size = file.tell()
                    progress = int(downloaded_size / total_size * 100)
                    print(f'\rDownloading {filename}: {progress}%', end='')
            print()
            return os.path.join(DLS, filename)
        else:
            print('Invalid Content-Type:', r.headers['Content-Type'])
            exit(1)


def prompt_overwrite(dest):
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
