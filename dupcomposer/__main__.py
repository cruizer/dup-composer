#!/usr/bin/env python3
"""Launch dupcomposer (CLI entrypoint)."""
import sys
import getopt
import os.path
import shutil
import subprocess
from dupcomposer.backup_runner import read_config, BackupRunner
from dupcomposer.backup_config import BackupConfig


def main():
    check_duplicity_version(get_terminal_encoding())
    # default config file to look for
    config_file = 'dupcomposer-config.yml'
    dry_run = False
    skip_config_safeguard = False
    full_backup = False
    # Collecting and parsing options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:dhsf')
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(1)

    for opt, a in opts:
        # Use specific config file
        if opt == '-c':
            if os.path.isfile(a):
                config_file = a
            else:
                usage()
                raise FileNotFoundError("Configuration file {} doesn't exist!"
                                        .format(a))
        # Simply output the duplicity commands, don't execute
        elif opt == '-d':
            dry_run = True
        # Skip config change test
        elif opt == '-s':
            skip_config_safeguard = True
        elif opt == '-f':
            full_backup = True
        elif opt == '-h':
            usage()
            sys.exit(0)

    if not args or args[0] not in ['backup', 'restore']:
        print('backup|restore action is missing from the command!')
        usage()
        sys.exit(1)
        
    if full_backup and args[0] == 'restore':
        print('-f: force full backup is an invalid option for a restore.')
        usage()
        sys.exit(1)

    config_raw =  read_config(config_file)
    # Check if groups requested are valid
    for group in args[1:]:
        if group not in config_raw.get('backup_groups', {}):
            raise ValueError('No group {} in the configuration!'.format(group))
    # Check if any of the existing groups have changed
    if not skip_config_safeguard:
        check_config_change(config_raw, config_file)
    # Setting up the environment
    config = BackupConfig(config_raw)
    runner = BackupRunner(config, args[0], full_backup)

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
        runner.run_cmds(args[1:])
        # Cache current run's config so that we can compare later
        save_config_cache(config_file)


def usage():
    print("""-----
usage: dupcomp.py [-d] [-s] [-f] [-c <configpath>] backup|restore [backup_group1 backup_group2 ...]

optional arguments:
 -d                dry run (just print the commands to be executed)
 -c <configpath>   use the configuration file at <configpath>
 -s                skip the configuration change safeguard step
 -f                force full backup
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
        major, minor, patch = map(int, result.stdout.split(b' ')[-1].split(b'.')[:3])
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


def check_config_change(config_data, config_filename):
    """Prints a message and exits on config change."""
    cache_filename = '.'.join([config_filename, 'cached'])
    if os.path.isfile(cache_filename):
        cached_groups = read_config(cache_filename).get('backup_groups', {})
        current_groups = config_data.get('backup_groups', {})
        changed_groups = []
        # We need the group names in a deterministic order
        # in the output for testing.
        for group_name in sorted(current_groups.keys()):
            if group_name in cached_groups and \
               current_groups[group_name] != cached_groups[group_name]:
                changed_groups.append(group_name)
        # At least one group changed, abort.
        if changed_groups:
            print('The configuration of existing group(s) '
                  '%s have changed! Backup aborted.\n\n'
                  'If you are certain, that no backup sets will '
                  'be impacted unintentionally by this change, '
                  'rerun dupcomp with the \'-f\' flag that skips '
                  'this safeguard step. You might want to consider '
                  'doing a dry run first, to verify how duplicity '
                  'will be run after the change.' % ', '.join(changed_groups))
            exit(1)


def save_config_cache(file_path):
    shutil.copyfile(file_path, '.'.join([file_path, '.cached']))


if __name__ == '__main__':
    main()
