import yaml
from dupcomposer import backup_config

def read_config(file_path):
    with open(file_path) as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    return config

class BackupRunner:

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
        cmds = {}
        for group in self.config.groups:
            opts =  group.get_opts_raw(self.mode)
            for i in range(len(opts)):
                opts[i][:0] = ['duplicity']
                opts[i] = ' '.join(opts[i])
            cmds[group.name] = opts
        return cmds
