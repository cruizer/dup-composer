#!/usr/bin/env python3
"""Launch dupcomposer (CLI entrypoint)."""
import sys
import getopt
import os.path
import subprocess
from dupcomposer.backup_runner import read_config, BackupRunner
from dupcomposer.backup_config import BackupConfig


def main():
    check_duplicity_version(get_terminal_encoding())
    # default config file to look for
    config_file = 'dupcomposer-config.yml'
    dry_run = False
    # Collecting and parsing options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:dh')
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(1)

    for opt, a in opts:
        if opt == '-c':
            if os.path.isfile(a):
                config_file = a
            else:
                usage()
                raise FileNotFoundError("Configuration file {} doesn't exist!"
                                        .format(a))
        elif opt == '-d':
            dry_run = True

    if not args or args[0] not in ['backup', 'restore']:
        print('backup|restore action is missing from the command!')
        usage()
        sys.exit(1)
        
    config_raw =  read_config(config_file)
    # Check if groups requested are valid
    for group in args[1:]:
        if group not in config_raw.get('backup_groups', {}):
            raise ValueError('No group {} in the configuration!'.format(group))

    # Setting up the environment
    config = BackupConfig(config_raw)
    runner = BackupRunner(config,args[0])

    # Do the actual run
    if dry_run:
        commands = runner.get_cmds_raw(args[1:])
        # Sorting keys for consistent ordering of output (for functional tests).
        for group in sorted(commands):
            print('Generating commands for group {}:\n'.format(group))

            for cmd in commands[group]:
                print(' '.join(cmd))

            print()
    else:
        # True run
        runner.run_cmds()
def usage():
    print("""-----
usage: dupcomp.py [-d] [-c <configpath>] backup|restore

optional arguments:
 -d                dry run (just print the commands to be executed)
 -c <configpath>   use the configuration file at <configpath>
-----""")


def check_duplicity_version(codec):
    """Verify that the correct version of duplicity is available.

    :param codec: The character encoding of the terminal.
    :ptype codec: str
    """
    try:
        result = subprocess.run(BackupRunner.command + ['--version'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    except FileNotFoundError as err:
        print('duplicity executable not found!\n\n'
              'Please make sure, that Duplicity is installed and is on your PATH.')
        exit(1)

    if result.returncode != 0:
        print('Executing "duplicity --version" has failed!\n'
              'Output:\n\n%s' % '\n'.join([result.stdout.decode(codec),
                                           result.stderr.decode(codec)]))
        exit(1)
    else:
        major, minor, patch = map(int, result.stdout.split(b' ')[-1].split(b'.'))
        if major == 0 and minor < 7:
            print('Unsupported Duplicity version %d.%d.%d!\n\n'
                  'Please install Duplicity 0.7 or later.' % (major, minor, patch))
            exit(1)

def get_terminal_encoding():
    """Returns the parent shell's character encoding.

    or 'utf-8' if the LANG environment variable is
    unavailable.
    """
    env_encoding = os.environ.get('LANG', None)
    if env_encoding:
        return env_encoding.split('.')[1].lower()
    else:
        return 'utf-8'

if __name__ == '__main__':
    main()
