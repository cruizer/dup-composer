
"""Run the backup and related system IO.

Classes:

BackupRunner: Fetch the duplicity commands and process them.

Functions:

read_config: Read the configuration file and load the YAML data.
"""
import yaml
import time
import subprocess
import os
from dupcomposer import backup_config

def read_config(file_path):
    """Read the configuration file and load the YAML data.

    :param file_path: The path of the YAML config file.
    :type file_path: str
    :return: The complete configuration data loaded into a dictionary.
    :rtype: dict
    """
    with open(file_path) as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    return config

class BackupRunner:
    """Collect the Duplicity commands and execute the backups.

    :param config: Processed configuration object.
    :type config: :class:`backup_config.BackupConfig`
    :param mode: The execution mode (Duplicity command) to execute.
    :type mode: str
    :param is_full_backup: Force full backup?
    :type is_full_backup: bool
    """
    command = ['duplicity']

    def __init__(self, config, mode, is_full_backup=False):
        self.base_cmd = 'duplicity'
        self.is_full_backup = is_full_backup
        if isinstance(config, backup_config.BackupConfig):
            self.config = config
        else:
            raise ValueError('First parameter is not a BackupConfig object.')
        self.valid_modes = ('backup', 'restore')
        if mode in self.valid_modes:
            self.mode = mode
        else:
            raise ValueError('{} is not a valid run mode.'.format(mode))

    def get_cmds_raw(self, group_names=None):
        """Get the Duplicity command lists for each group.

        It returns a dictionary with the config group names as keys.
        Each key has a list as its value and the list contains the
        Duplicity commands partitioned in a list.

        :param group_names: The group names to give the commands for.
        :type group_names: list
        :return: The Duplicity commands for each backup group.
        :rtype: dict
        """
        cmds = {}
        for group in self.config.groups:
            if not group_names or group in group_names:
                opts =  self.config.groups[group].get_opts_raw(self.mode)
                for i in range(len(opts)):
                    # We prepend the options if full is forced.
                    if self.is_full_backup and self.mode == 'backup':
                        opts[i][:0] = ['full']
                    # BackupGroup only returns the options,
                    # so prepend with the actual command.
                    opts[i][:0] = BackupRunner.command
                cmds[group] = opts
        return cmds

    def run_cmds(self, group_names=None):
        """Execute the Duplicity commands.

        :param group_names: The group names to execute.
        :type group_names: list
        """
        commands = self.get_cmds_raw(group_names)
        for group in sorted(commands):
            print('Running backups for group: {}'.format(group))
            print('==\n==')
            # Process the commands for the given group.
            self._run_group_cmds(commands, group)

    def _run_group_cmds(self, commands, group):
        """Execute the Duplicity commands for a group.

        For each command it prints the command to be run, then
        executes it.

        :param commands: A list of command argument lists for the given group..
        :type commands: list
        :param group: The name of the group.
        :type group: str
        """
        for cmd in commands[group]:
            print('Executing Duplicity command: {}'.format(' '.join(cmd)))
            print('==\nDuplicity output follows:\n==\n')
            # Call the function actually creating the process.
            self._run_cmd(cmd, self.config.groups[group].get_env())


    def _run_cmd(self, command, env):
        """Execute the duplicty command.

        This does the actual work to run the duplicity process.
        It prints the output fetched from Duplicity and prints the result -
        success or failure - to the console.

        :param command: The command argument list.
        :type command: list
        """
        env_complete = dict(os.environ)
        env_complete.update(env)
        proc = subprocess.Popen(command,
                                env=env_complete,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)
        while True:
            try:
                print(proc.stdout.readline(), end='')
            except Exception:
                proc.kill()
                break
            if proc.poll() is not None:
                print(proc.stdout.read())
                print('== End of Duplicity output ==')
                if proc.returncode == 0:
                    print('Duplicity returned NORMALLY.\n')
                else:
                    print('Duplicity returned with ERROR CODE {}'.format(proc.returncode))
                break
            time.sleep(1)
