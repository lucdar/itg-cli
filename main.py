import argparse
import os
from commands.add_song import add_song
from commands.add_pack import add_pack
from commands.utils.constants import TEMP_ROOT, COURSES


def main():
    ### Commands Format ###
    # 'command': (help, [(arg1, help1), (arg2, help2), ...])
    commands = {
        'add-pack': ('Add a pack from a supplied zip file or link',
                     [('path', 'path or url to pack')]),
        'add-song': ('Add a song from a supplied zip file or link',
                     [('path', 'path or url to song')]),
        'config': ('Set the current profile',
                   [('profile', 'profile to use')]),
        'ping': ('Responds with pong :3', []),
        'restart': ('(Re)start the game', []),
        'songlist': ('Update the current songlist', []),
        'stop': ('Stop the game', [])
    }

    parser = argparse.ArgumentParser(description='ITG CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)
    for (command, (command_help, args)) in commands.items():
        subparser = subparsers.add_parser(command, help=command_help)
        for (arg, arg_help) in args:
            subparser.add_argument(arg, help=arg_help)

    args = parser.parse_args()

    # create temp folder if it doesn't exist
    if not os.path.exists(TEMP_ROOT):
        os.mkdir(TEMP_ROOT)
    if not os.path.exists(COURSES):
        os.mkdir(COURSES)

    # run command based on supplied arguments
    match args.command:
        case 'add-pack':
            add_pack(args)
        case 'add-song':
            add_song(args)
        case 'config':
            ...
        case 'ping':
            print('pong')
        case 'restart':
            ...
        case 'songlist':
            ...
        case 'stop':
            ...


if __name__ == '__main__':
    main()
