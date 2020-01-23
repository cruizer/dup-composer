"""Process the configuration and generate Duplicity options from that.

Classes:

BackupConfig: Represent the whole configuration and generate the groups.
BackupGroup: Orchestrate the backup for the given config group.
BackupEncryption: Handle the backup GPG encryption options.
BackupProvider: Abstract class and factory for the following classes:
    BackupProviderLocal: Local file system target options.
    BackupProviderS3: S3 bucket target options.
    BackupProviderSSH: SFTP/SCP target options.
BackupSource: Backup/restore path options.
BackupFilePrefixes: Handle the file prefixing for backup files.
"""
import re
from dupcomposer import backup_keyring

class BackupConfig:
    """Generate the backup groups from the config data and store them.

    :param config_data: Raw data generated from the config file.
    :type config_data: dict
    """
    def __init__(self, config_data):
        self.config_data = config_data
        self.groups = {}
        self.createGroups()

    def createGroups(self):
        """Generate a list of :class:`BackupGroup` objects."""
        groups_conf = self.config_data['backup_groups']
        for group_name in groups_conf:
            self.groups[group_name] = BackupGroup(groups_conf[group_name], group_name)

class BackupGroup:
    """Orchestrate the backup options for the given config group.

    :param group_data: Raw config data for the given group.
    :type group_data: dict
    :param group_name: The name of the group in the configuration.
    :type group_name: str
    """
    def __init__(self, group_data, group_name):
        self.group_data = group_data
        self.name = group_name
        self._keyring = None
        self.mandatory_datakeys = ['encryption',
                                   'backup_provider',
                                   'sources',
                                   'volume_size']
        
        for  i in self.mandatory_datakeys:
            if i not in self.group_data:
                raise KeyError('Invalid backup group configuration data')

        self.encryption = BackupEncryption(group_data['encryption'], self)
        self.provider = BackupProvider.factory(group_data['backup_provider'], self)
        self._setup_prefixes()
        self._setup_sources()
        self.volsize = group_data['volume_size']


    @property
    def keyring(self):
        if not self._keyring:
            self._build_keyring()
        return self._keyring


    def _build_keyring(self):
        config = self.group_data.get('keyring', {})
        self._keyring = backup_keyring.BackupKeyring(**config)


    def get_opts_raw(self, mode):
        """Get the Duplicity command line options for all sources.

        :param mode: Duplicity command, either 'backup' or 'restore'.
        :type mode: str
        :return: A list of CLI option lists for all sources (paths).
        :rtype: list
        """
        opts_all = []
        for source in self.sources:
            # Chain the CLI options.
            opts_all.append(self.encryption.get_cmd() + self._get_volume_cmd() +
                             self.prefix.get_cmd() + source.get_cmd(mode))
        return opts_all

    def get_env(self):
        """Get all the environment variable data for the given group.

        :return: A dictionary with the env. variable names as keys.
        :rtype: dict
        """
        env_all = {}
        # Merge the environment variable dicts into a master.
        env_all.update(self.provider.get_env())
        env_all.update(self.encryption.get_env())
        return env_all

    def _get_volume_cmd(self):
        """Generate the volsize CLI option"""
        return ['--volsize', str(self.volsize)]

    def _setup_sources(self):
        """Instantiate :class:`BackupSource` objects for the group."""
        self.sources = []
        sources_data = self.group_data['sources']
        # We sort it for consistency with the test fixtures.
        for k in sorted(sources_data.keys()):
            self.sources.append(BackupSource(k, sources_data[k], self.provider))

    def _setup_prefixes(self):
        """Instantiate :class:`BackupFilePrefixes` objects for the group"""
        self.prefix = BackupFilePrefixes(self.group_data.get('backup_file_prefixes', None))

class BackupEncryption:
    """Handle the GPG encryption.

    :param encryption_data: The raw configuration for the encryption.
    :type encryption_data: dict

    :param backup_group: The backup configuration group object.
    :type backup_group: BackupGroup
    """
    def __init__(self, encryption_data, backup_group=None):

        self.backup_group = backup_group
        self._set_enabled_flag(encryption_data)
        self._set_gpg_params(encryption_data)
        
    def get_cmd(self):
        """Get the encryption CLI options.

        :return: A list of Duplicity CLI options.
        :rtype: list"""
        if self.enabled == False:
            return ['--no-encryption']
        else:
            return ['--encrypt-key {}'.format(self.gpg_key),
                    '--sign-key {}'.format(self.gpg_key)]

    def get_env(self):
        """Get the shell env. variables for the encryption.

        :return: A dictionary with the variable name as key.
        :rtype: dict
        """
        if self.enabled == False:
            return {}
        else:
            return {'PASSPHRASE': self.gpg_passphrase}

    def _set_enabled_flag(self, encryption_data):
        """Check if the flag in the config is valid and set it.

        Set flag on attribute self.enabled as a side effect.

        :param encryption_data: Raw encryption related config.
        :type encryption_data: dict
        :raises ValueError: Raised if the flag is not a boolean.
        """
        if encryption_data['enabled'] in (True, False):
            self.enabled = encryption_data['enabled']
        else:
            raise ValueError('Encryption is neither enabled nor disabled: {}'.format(encryption_data))

    def _set_gpg_params(self, encryption_data):
        """Set parameters required for encryption.

        Set values on attributes self.gpg_key and self.gpg_passphrase
        as a side effect.

        :param encryption_data: Raw encryption related config.
        :type encryption_data: dict
        """
        # For encryption to work, we need both the key and the passphrase.
        if self.enabled and {'gpg_key', 'gpg_passphrase'} < set(encryption_data.keys()):
            self.gpg_key = encryption_data['gpg_key']
            self._set_passphrase(encryption_data['gpg_passphrase'])
        elif not self.enabled:
            self.gpg_key = self.gpg_passphrase = None
        else:
            raise ValueError('Encryption is enabled, but GPG keys are missing.')


    def _set_passphrase(self, pp_config):
        """Set the passphrase, get it from keyring if needed.

        :param pp_config: Either the passphrase itself, or a list with two
                          members specifying the keyring service and account.
        :type pp_config: str, list
        """
        if isinstance(pp_config, str):
            self.gpg_passphrase = pp_config
        elif isinstance(pp_config, list) and len(pp_config) == 2 \
             and hasattr(self.backup_group, 'keyring'):
            self.gpg_passphrase = self.backup_group.keyring.get_secret(pp_config)
        else:
            raise ValueError('Unable to get/set '
                             'passphrase with data: %s' % pp_config)

class BackupProvider:
    """Abstract and factory class for specialized providers.

    DO NOT instantiate this, use the factory() method to create the
    appropriate subclass instead.

    :param provider_data: Raw provider data.
    :type provider_data: dict
    :param backup_group: Group config object.
    :type backup_group: BackupGroup
    """
    def __init__(self, provider_data, backup_group=None):
        self.url = provider_data['url']
        self.backup_group = backup_group

    @classmethod
    def factory(cls, provider_data, backup_group=None):
        """Generate the appropriate provider subclass.

        :param provider_data: Raw provider data.
        :type provider_data: dict
        :param backup_group: Group config object
        :type keyring_provider: BackupGroup
        :raises KeyError: if the key 'url' is missing from provider_data
        :raises ValueError: if the URL scheme is not recognized.
        :return: The appropriate provider subclass.
        :rtype: :class:`BackupProviderLocal`, :class:`BackupProviderS3`,
                :class:`BackupProviderSSH`
        """
        url = provider_data['url']
        
        if re.search('^file://.*', url):
            return BackupProviderLocal(provider_data)
        elif re.search('^s3://.*', url):
            return BackupProviderS3(provider_data, backup_group)
        elif re.search('^scp://.*', url) or re.search('^sftp://.*', url):
            return BackupProviderSSH(provider_data, backup_group)
        else:
            raise ValueError("URL {} is not recognized.".format(url))

    def get_cmd(self, path):
        """Append the source backup path to the provider URL scheme
        :param path: the backup path
        :type path: str
        :return: The full backup path to backup to / restore from.
        :rtype: str
        """
        # strip and readd "/" with join in case it
        # is missing from the end of the URL.
        if self.url[-1] == '/':
            return ''.join([self.url, path])
        else:
            return ''.join([self.url + '/', path])

    def get_env(self):
        # TODO: Indicate that this is an abstract method.
        pass


    def _load_secret(self, secret_def):
        """Determine the secret type and load from the keyring is needed.

        :param secret_def: The configuration value decribing the secret.
        :type secret_def: str, list
        """
        # We return the plaintext secret as-is
        if isinstance(secret_def, str):
            return secret_def
        # We read the secret from the keyring
        elif isinstance(secret_def, list) and len(secret_def) == 2 \
             and hasattr(self.backup_group, 'keyring'):
            return self.backup_group.keyring.get_secret(secret_def)
        else:
            raise ValueError('Invalid secret configuration: %s' % secret_def)


class BackupProviderLocal(BackupProvider):
    """Local filesystem backup target provider.

    :param provider_data: Raw provider data.
    :type provider_data: dict
"""
    def __init__(self, provider_data):
        super().__init__(provider_data)

    def get_env(self):
        """Get shell environment for local the local provider.

        :return: an empty dictionary as no env. variable needed.
        :rtype: dict
        """
        return {}
        
class BackupProviderS3(BackupProvider):
    """AWS S3 backup target provider.

    :param provider_data: Raw provider data.
    :type provider_data: dict
    :param backup_group: Group config object
    :type backup_group: BackupGroup
    """
    def __init__(self, provider_data, backup_group):
        super().__init__(provider_data, backup_group)
        self.access_key = provider_data['aws_access_key']
        self.secret_key = self._load_secret(provider_data['aws_secret_key'])


    def get_cmd(self, path):
        """Append the backup path to the target URL scheme.

        This makes relative and absolute backup paths indifferent, as
        the full URL can only be specified relative to the bucket.

        :param path: the backup path
        :type path: str
        :return: The full backup path to backup to / restore from.
        :rtype: str
        """
        # Ensure, that only one slash separates the URL scheme and the path.
        return '/'.join([self.url.rstrip('/'),
                         path.lstrip('/')])


    def get_env(self):
        """Get the shell env. variables for AWS S3

        :return: The environent variables with the AWS credentials.
        :rtype: dict
        """
        return {'AWS_ACCESS_KEY': self.access_key,
                'AWS_SECRET_KEY': self.secret_key}

class BackupProviderSSH(BackupProvider):
    """SFTP/SCP backup target provider.

    :param provider_data: Raw provider data.
    :type provider_data: dict
    :param backup_group: Group config object
    :type backup_group: BackupGroup
    """
    def __init__(self, provider_data, backup_group):
        super().__init__(provider_data, backup_group)
        self.password = provider_data.get('password', None)
        # If we have password data, we need to run it through the loader
        if self.password:
            self.password = self._load_secret(self.password)


    def get_env(self):
        """Get the shell env. variable for SSH backup.

        :return: The env. variable with the SSH password.
        :rtype: dict
        """
        if self.password:
            return {'FTP_PASSWORD': self.password}
        else:
            return {}

class BackupSource:
    """Path object for the source, backup and restore target.

    :param source_path: The path to be backed up.
    :type source_path: str
    :param config: raw config data for the target of the backup/restore.
    :type config: dict
    :param provider: The URL scheme target to backup to / restore from.
    :type provider: class:`BackupProviderLocal`, class:`BackupProviderS3`,
                    class:`BackupProviderSSH`
    :raises ValueError: if the source or backup path is empty.
    """
    def __init__(self, source_path, config, provider):
        self.source_path = source_path
        self.backup_path = config['backup_path']
        self.restore_path = config.get('restore_path', None)
        self.provider = provider
        if (len(self.source_path) == 0 or 
            len(self.backup_path) == 0):

            raise ValueError('Empty path is not allowed.')
        self._check_forbidden_chars()
            
    def get_cmd(self, mode='backup'):
        """Get the source and target path for the given action.

        The provider will append the backup_path to the provider URL
        scheme, to form the fully qualified path to backup to or
        restore from.

        :param mode: Duplicity command, either 'backup' or 'restore'.
        :type mode: str
        :raises ValueError: if the mode is neither 'backup' nor 'restore',
                            or if no restore path is defined and we do
                            a restore.
        :return: A list of the source and backup; backup and restore
                 path, depending on the mode (action).
        :rtype: list
        """
        # The Duplicity action is determined by the URL / path order.
        if mode == 'backup':
            return [self.source_path,
                    self.provider.get_cmd(self.backup_path)]
        elif mode == 'restore':
            if not self.restore_path:
                raise ValueError('Restore path is not defined in the configuration.')
            return [self.provider.get_cmd(self.backup_path),
                    self.restore_path]
        else:
            raise ValueError('Invalid mode parameter.')

    def _check_forbidden_chars(self):
        # Detect control chars + backslash
        for p in [self.source_path,
                  self.backup_path,
                  self.restore_path]:
            # In case restore_path is empty
            if not p: continue
            if (p[0] == '-' or
                re.search(r'[\x00-\x1f\x7f\\]', p)):

                raise ValueError('Leading hyphens, control characters '
                                 'and backslash are not allowed in '
                                 'the path configuration.')

class BackupFilePrefixes:
    """Determine the prefix of the archive, manifest and signature files.

    :param config: The raw prefix configuration or None if no prefix.
    :type config: dict, None
    """
    def __init__(self, config):
        self.valid_types = ('manifest', 'archive', 'signature')
        self.config = config
        self.prefix_commands = []
        # If we have data, generate the cmd string.
        if config is not None:
            self._generate_commands()

    def get_cmd(self):
        """Get the Duplicity CLI options for file prefixes.

        :return: a list of the prefix CLI options.
        :rtype: list
        """
        return self.prefix_commands

    def _generate_commands(self):
        """Iterate through the file prefix config
        and generate the CLI options.

        Side effect (and purpose) of this method is to populate the
        self.prefix_commands list with the relevant CLI options.
        """
        # Sort the keys for consistent test results with fixtures.
        for k in sorted(self.config.keys()):
            if k in self.valid_types:
                self.prefix_commands.extend(['--file-prefix-{}'.format(k), self.config[k]])
            else:
                raise ValueError('{} is not a valid prefix option.'.format(k))

