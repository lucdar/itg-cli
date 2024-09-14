import argparse
from commands.add_song import add_song
from commands.add_pack import add_pack
from commands.censor import censor, uncensor


subparser_dict = {
    "add-pack": (
        {"help": "Add a pack from a supplied directory or link"},
        {
            "path": {"help": "path or url to pack"},
            "--overwrite": {
                "help": "skip overwrite confirmation",
                "action": "store_true",
            },
        },
    ),
    "add-song": (
        {"help": "Add a song from a supplied directory or link"},
        {
            "path": {"help": "path or url to song"},
            "--overwrite": {
                "help": "skip overwrite confirmation",
                "action": "store_true",
            },
        },
    ),
    "censor": (
        {"help": "Move a song from the songs folder to the quarantine folder"},
        {"path": {"help": "path to song to quarantine"}},
    ),
    "uncensor": (
        {
            "help": "Displays a list of quarantined songs. Select a song to move back to the songs folder."
        },
        {},
    ),
    "ping": ({"help": "responds with pong :3"}, {}),
}

def main():
    parser = argparse.ArgumentParser(description="ITG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True, )
    for subcommand, (kwargs, subcommand_args) in subparser_dict.items():
        subparser = subparsers.add_parser(subcommand, **kwargs)
        for arg, kwargs in subcommand_args.items():
            subparser.add_argument(arg, **kwargs)

    args = parser.parse_args()

    match args.command:
        case "add-pack":
            add_pack(args)
        case "add-song":
            add_song(args)
        case "censor":
            censor(args)
        case "uncensor":
            uncensor()
        case "ping":
            print("pong")


if __name__ == "__main__":
    main()
