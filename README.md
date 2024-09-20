# itg-cli

Command line interface that automates & simplifies common administrative tasks for Stepmania or its derivatives.

## Setup

This project does not have a build system configured (next thing on the todo list!), so here are some basic instructions to get it up and running.

```Bash
# Clone the repository to your machine
git clone https://github.com/lucdar/itg-cli
cd itg-cli

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the CLI
python main.py ping
```

Depending on your OS/environment you may need to use `python3` in place of `python` or `pip3` in place of `pip`.

## Configuring

[`settings_template.toml`](settings_template.toml) contains empty fields for you to fill in. You may edit the file in-place or copy and rename it to `settings.toml` which is included in [`.gitignore`](.gitignore) (helpful for development).

## Usage

* `add-pack` adds a pack from the supplied path or link to your configured `packs` directory.
  
    ```Bash
    # Supports links to local .zip files
    python main.py add-pack path/to/pack.zip
    # Or local directories:
    python main.py add-pack path/to/pack/

    # Supports links to .zip files
    python main.py add-pack https://omid.gg/THC
    # Google drive links sometimes contain special characters, so they should be surrounded in quotes
    python main.py add-pack "https://drive.google.com/file/d/18XoCKcA7N4ptE6U7wOJIJgfVwTAyuA10/view"
    ```

* `add-song` adds a song from the supplied path or link to your configured `singles` directory.

    ```Bash
    # Supports links to local .zip files
    python main.py add-song path/to/song.zip
    # Or local directories:
    python main.py add-song path/to/song/
    # Supports links to .zip 
    python main.py add-song 
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

## Contributing

This project is under active development, and my first published/marketed open source project, so I'm still learning how all this works in practice. That being said, I'm open PRs or feature requests, though this may change in the future.

## License

[MIT](https://choosealicense.com/licenses/mit/)
