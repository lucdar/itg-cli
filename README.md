# itg-cli

`itg-cli` is a command line interface that automates & simplifies common
administrative tasks for Stepmania or its derivatives. Its functionality can
also be imported as a package for use in a Python project.

## Setup

Make sure you have python 3.9 or newer installed.

```Bash
$ python --version
Python 3.9.20
```

Install via pipx (recommended):

1. Install [pipx](https://pipx.pypa.io/stable/)

2. ```Bash
   pipx install itg-cli
   ```

Install via pip (for use as a module):

```Bash
pip install itg-cli
```

```python
from itg_cli import *
from pathlib import Path

packs = Path("/path/to/packs")
courses = Path("/path/to/courses")

add_pack("https://omid.gg/THC", packs, courses)
```

## Configuring

`itg-cli` will generate a config file if one is not found at the default
location. This location and the default values vary depending on the platform
(see below). The location of the created config file will be output by the
program after it's created.

The `init-config` command is used to write a default config file to a location
of your choice (or the default location if none is supplied). You can supply
this config file to other commands by passing it using the `--config`
parameter.

If your itgmania data folder location is not listed below (e.g. you are using a
portable install), you will need to manually edit this config file in the text
editor of your choice.

```plaintext
Windows: %appdata%\ITGMania
Linux: ~/.itgmania
MacOS: ~/Library/Application Support/ITGMania
    MacOS cache: ~/Library/Caches/ITGMania
```

## Usage

* `add-pack` adds a pack from the supplied path or link to your configured `packs` directory.
  
    ```Bash
    # Supports links to local .zip files
    itg-cli add-pack path/to/pack.zip
    # Or local directories:
    itg-cli add-pack path/to/pack/

    # Supports links to .zip files
    itg-cli add-pack https://omid.gg/THC
    # Google drive links sometimes contain special characters, so they should be surrounded in quotes
    itg-cli add-pack "https://drive.google.com/file/d/18XoCKcA7N4ptE6U7wOJIJgfVwTAyuA10/view"
    ```

* `add-song` adds a song from the supplied path or link to your configured `singles` directory.

    ```Bash
    # Supports links to local .zip files
    itg-cli add-song path/to/song.zip
    # Or local directories:
    itg-cli add-song path/to/song/
    # Supports links to .zip files
    itg-cli add-song "https://cdn.discordapp.com/attachments/529867916833718294/1286510412262805524/Love_Bomb.zip?ex=66ee2bb0&is=66ecda30&hm=6c6ac229657a01b0f48995ed236a22889502c5407478cfe6151596f4355ca7b4&"
    ```

* `censor` Move a song in your packs folder to packs/.censored/\[pack]/\[SongFolder], hiding it from players.

    ```Bash
    itg-cli censor "path/to/Songs/7gays1pack/Stupid Hoe/"
    ```

* `uncensor` displays a list of songs that have been censored and prompts you to select a file to uncensor.

    ```Bash
    $ itg-cli uncensor
    1. Monke Rave (Tech Heavy Charts)
    2. Stupid Hoe (7gays1pack)
    3. ME!ME!ME! (Anime Extravaganza 4)
    Select a song to uncensor (1-3): 1
    Uncensored Monke Rave from Tech Heavy Charts.
    ```

## Contributing

This project is my first published/marketed open source project, so I'm still
learning how all this works in practice. That being said, If you run into any bugs
or have ideas for new features, please feel free to create an [issue](https://github.com/lucdar/itg-cli/issues) or [pull request](https://github.com/lucdar/itg-cli/pulls).

## License

[MIT](https://choosealicense.com/licenses/mit/)
