import argparse
from commands.add_song import add_song


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
        'ping': ('Ping the server', []),
        'restart': ('(Re)start the game', []),
        'status': ('Get the current status of the game', []),
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

    # run command based on supplied arguments
    match args.command:
        case 'add-pack':
            ...
        case 'add-song':
            add_song(args)
        case 'config':
            ...
        case 'ping':
            print('pong')
        case 'restart':
            ...
        case 'status':
            ...
        case 'songlist':
            ...
        case 'stop':
            ...


if __name__ == '__main__':
    main()
