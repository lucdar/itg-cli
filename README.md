# itg-cli

Command line interface that automates & simplifies common administrative tasks for Stepmania or its derivatives. Can also be imported as a package for use in a python project.

## Setup

Make sure you have python 3.9 or newer installed.

```Bash
$ python --version
Python 3.9.20
```

Install via pip:

```Bash
pip install itg-cli
```

## Configuring

Running `itg-cli` with a command for the first time will generate a config file
at `~/.config/itg-cli.toml` and will populate it with a platform specific default
configuration (see below). If your itgmania installation location is not in the
default list below, you will need to manually edit this config file in the text
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

* `censor` moves a specified song within your `packs` directory to the configured `censored` directory, removing them from play. (defaults to itg-cli/.censored if unset)

    ```Bash
    itg-cli censor "path/to/7gays1pack/Stupid Hoe/"
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

* `ping` prints "pong" and exits

    ```Bash
    $ itg-cli ping
    pong
    ```

## Contributing

This project is under active development, and my first published/marketed open source project, so I'm still learning how all this works in practice. That being said, I'll try to respond to any PRs or issues, though this may change in the future.

## License

[MIT](https://choosealicense.com/licenses/mit/)
