import argparse
from commands.add_song import add_song
from commands.add_pack import add_pack
from commands.censor import censor, uncensor
from config import config_data

COURSES = config_data['courses']
TEMP_ROOT = config_data['temp_root']


def main():
    ### Commands Format ###
    # 'command': (help, [(arg1, help1), (arg2, help2), ...])
    commands = {
        'add-pack': (
            'Add a pack from a supplied zip file or link',
            [
                ('path', 'path or url to pack', 'store'),
                ('--force', 'skip confirmation', 'store_true')
            ]
        ),
        'add-song': (
            'Add a song from a supplied zip file or link',
            [
                ('path', 'path or url to song', 'store'),
                ('--force', 'skip confirmation', 'store_true')
            ]
        ),
        'censor': (
            'Remove a song from the songs folder and move it to the quarantine folder',
            [('path', 'path to song to quarantine', 'store')]
        ),
        'uncensor': (
            'Restore a song from the quarantine folder to the songs folder',
            []
        ),
        'ping': (
            'Responds with pong :3',
            []
        ),
    }

    parser = argparse.ArgumentParser(description='ITG CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)
    for (command, (command_help, args)) in commands.items():
        subparser = subparsers.add_parser(command, help=command_help)
        for (arg, arg_help, action) in args:
            subparser.add_argument(arg, help=arg_help, action=action)

    args = parser.parse_args()

    match args.command:
        case 'add-pack':
            add_pack(args)
        case 'add-song':
            add_song(args)
        case 'censor':
            censor(args)
        case 'uncensor':
            uncensor()
        case 'ping':
            print('pong')


if __name__ == '__main__':
    main()
