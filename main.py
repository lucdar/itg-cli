import argparse, simfile

def main():
    # get command using argparse
    parser = argparse.ArgumentParser(description='ITG CLI')
    parser.add_argument('command', help='command to run')
    args = parser.parse_args()

    # run command based on supplied arguments
    match args.command:
        case 'ping':
            print('pong')
            exit(0)

if __name__ == '__main__':
    main()