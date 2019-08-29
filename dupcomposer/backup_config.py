import re

class BackupConfig:
    def __init__(self, config_data):
        self.config_data = config_data
        self.groups = []
        self.createGroups()

    def createGroups(self):
        groups_conf = self.config_data['backup_groups']
        for group_name in groups_conf:
            self.groups.append(BackupGroup(groups_conf[group_name], group_name))

class BackupGroup:
    def __init__(self, group_data, group_name):
        self.group_data = group_data
        self.name = group_name
        self.mandatory_datakeys = ['encryption',
                                   'backup_provider',
                                   'sources',
                                   'volume_size']
        
        for  i in self.mandatory_datakeys:
            if i not in self.group_data:
                raise KeyError('Invalid backup group configuration data')

        self.encryption = BackupEncryption(group_data['encryption'])
        self.provider = BackupProvider.factory(group_data['backup_provider'])
        self._setup_prefixes()
        self._setup_sources()
        self.volsize = group_data['volume_size']

    def get_opts_raw(self, mode):
        opts_all = []
        for source in self.sources:
            opts_all.append(self.encryption.get_cmd() + self._get_volume_cmd() +
                             self.prefix.get_cmd() + source.get_cmd(mode))
        return opts_all

    def get_env(self):
        env_all = {}
        env_all.update(self.provider.get_env())
        env_all.update(self.encryption.get_env())
        return env_all

    def _get_volume_cmd(self):
        return ['--volsize', str(self.volsize)]

    def _setup_sources(self):
        self.sources = []
        sources_data = self.group_data['sources']
        for k in sorted(sources_data.keys()):
            self.sources.append(BackupSource(k, sources_data[k], self.provider))

    def _setup_prefixes(self):
            self.prefix = BackupFilePrefixes(self.group_data.get('backup_file_prefixes', None))

class BackupEncryption:
    def __init__(self, encryption_data):
        self._set_enabled_flag(encryption_data)
        self._set_gpg_params(encryption_data)
        
    def get_cmd(self):
        if self.enabled == False:
            return ['--no-encryption']
        else:
            return ['--encrypt-key {}'.format(self.gpg_key),
                    '--sign-key {}'.format(self.gpg_key)]

    def get_env(self):
        if self.enabled == False:
            return {}
        else:
            return {'PASSPHRASE': self.gpg_passphrase}

    def _set_enabled_flag(self, encryption_data):
        if encryption_data['enabled'] in (True, False):
            self.enabled = encryption_data['enabled']
        else:
            raise ValueError('Encryption is neither enabled nor disabled: {}'.format(encryption_data))

    def _set_gpg_params(self, encryption_data):
        if self.enabled and {'gpg_key', 'gpg_passphrase'} < set(encryption_data.keys()):
            self.gpg_key = encryption_data['gpg_key']
            self.gpg_passphrase = encryption_data['gpg_passphrase']
        elif not self.enabled:
            self.gpg_key = self.gpg_passphrase = None
        else:
            raise ValueError('Encryption is enabled, but GPG keys are missing.')

class BackupProvider:
    def __init__(self, provider_data):
        self.url = provider_data['url']

    @classmethod
    def factory(cls, provider_data):
        url = provider_data['url']
        
        if re.search('^file://.*', url):
            return BackupProviderLocal(provider_data)
        elif re.search('^s3://.*', url):
            return BackupProviderS3(provider_data)
        elif re.search('^scp://.*', url):
            return BackupProviderSCP(provider_data)
        else:
            raise ValueError("URL {} is not recognized.".format(url))

    def get_cmd(self, path):
        return ''.join([self.url, path])

    def get_env(self):
        pass

class BackupProviderLocal(BackupProvider):
    def __init__(self, provider_data):
        super().__init__(provider_data)

    def get_env(self):
        return {}
        
class BackupProviderS3(BackupProvider):
    def __init__(self, provider_data):
        super().__init__(provider_data)
        self.access_key = provider_data['aws_access_key']
        self.secret_key = provider_data['aws_secret_key']

    def get_cmd(self, path):
        return '/'.join([self.url.rstrip('/'),
                         path.lstrip('/')])

    def get_env(self):
        return {'AWS_ACCESS_KEY': self.access_key,
                'AWS_SECRET_KEY': self.secret_key}

class BackupProviderSCP(BackupProvider):
    def __init__(self, provider_data):
        super().__init__(provider_data)
        self.password = provider_data.get('password', None)

    def get_env(self):
        if self.password:
            return {'FTP_PASSWORD': self.password}
        else:
            return {}

class BackupSource:
    def __init__(self, source_path, config, provider):
        self.source_path = source_path
        self.backup_path = config['backup_path']
        self.restore_path = config['restore_path']
        self.provider = provider
        if (len(self.source_path) == 0 or 
            len(self.backup_path) == 0 or
            len(self.restore_path) == 0):

            raise ValueError('Empty path is not allowed.')
            
    def get_cmd(self, mode='backup'):
        if mode == 'backup':
            return [self.source_path,
                    self.provider.get_cmd(self.backup_path)]
        elif mode == 'restore':
            return [self.provider.get_cmd(self.backup_path),
                    self.restore_path]
        else:
            raise ValueError('Invalid mode parameter.')

class BackupFilePrefixes:
    def __init__(self, config):
        self.valid_types = ('manifest', 'archive', 'signature')
        self.config = config
        self.prefix_commands = []
        # If we have data, generate the cmd string
        if config is not None:
            self._generate_commands()

    def get_cmd(self):
        return self.prefix_commands

    def _generate_commands(self):
        for k in sorted(self.config.keys()):
            if k in self.valid_types:
                self.prefix_commands.extend(['--file-prefix-{}'.format(k), self.config[k]])
            else:
                raise ValueError('{} is not a valid prefix option.'.format(k))

