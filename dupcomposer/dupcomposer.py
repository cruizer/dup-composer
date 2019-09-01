"""Run the backup and related system IO.

Classes:

BackupRunner: Fetch the duplicity commands and process them.

Functions:

read_config: Read the configuration file and load the YAML data.
"""
import yaml
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
    """
    def __init__(self, config, mode):
        self.base_cmd = 'duplicity'
        if isinstance(config, backup_config.BackupConfig):
            self.config = config
        else:
            raise ValueError('First parameter is not a BackupConfig object.')
        self.valid_modes = ('backup', 'restore')
        if mode in self.valid_modes:
            self.mode = mode
        else:
            raise ValueError('{} is not a valid run mode.'.format(mode))

    def get_cmds_raw(self):
        """Get the Duplicity command lists for each group.

        It returns a dictionary with the config group names as keys.
        Each key has a list as its value and the list contains the
        Duplicity commands partitioned in a list.

        :return: The Duplicity commands for each backup group.
        :rtype: dict
        """
        cmds = {}
        for group in self.config.groups:
            opts =  group.get_opts_raw(self.mode)
            for i in range(len(opts)):
                opts[i][:0] = ['duplicity']
                opts[i] = ' '.join(opts[i])
            cmds[group.name] = opts
        return cmds
