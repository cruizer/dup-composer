import keyring
import os
import stat
import pwd


class BackupKeyring:
    """Manage interactions for secrets used by backup groups.

    It picks up the UID and the DBUS_SESSION_BUS_ADDRESS in the
    running user's environment. This is considered as the default
    when reading secrets, but this can be overridded with a special
    configuration when instantiating BackupKeyring.

    :param user: The name of the keyring's user, we will read from.
    : type user: str

    :param bus: The socket path used to communicate with DBUS the
                keyring is listening on. This parameter is MANDATORY
                when a username is provided upon instantiation.
    """
    # The UID of the user running the script,
    runuser_id = os.geteuid()
    # The socket address of the DBUS the Gnome Keyring
    # is listening on for the user running the script.
    runuser_bus = os.environ.get('DBUS_SESSION_BUS_ADDRESS', None)
    if not isinstance(keyring.get_keyring(),
                      keyring.backends.SecretService.Keyring):
        keyring.set_keyring(keyring.backends.SecretService.Keyring())


    def __init__(self, user=None, bus=None):
        self.uid = None
        self.bus = None
        if user and not bus:
            raise ValueError('No bus provided for %s.' % user)
        self._init_special_user(user)
        self._init_special_socket(bus)
        if not self.bus:
            raise ValueError('Mission DBUS address! Please check the '
                             'DBUS_SESSION_BUS_ADDRESS environment '
                             'variable, or provide a bus address in '
                             'the Dupcomposer configuration.')


    def _init_special_user(self, username):
        """Set the configured user
        """
        if username:
            self.uid = pwd.getpwnam(username).pw_uid
        else:
            self.uid = BackupKeyring.runuser_id


    def _init_special_socket(self, socket_address):
        """Check and set the DBUS socket
        """
        if socket_address:
            mode = os.stat(socket_address).st_mode
            if stat.S_ISSOCK(mode) == False:
                raise OSError('Path %s is not a socket.' % socket_address)
            self.bus = '='.join(['unix:path',socket_address])
        else:
            self.bus = BackupKeyring.runuser_bus


    def get_secret(self, ks_entry):
        """Read from the keyring and return the secret string.

        The secret string can contain a password, passphrase or any string
        that is stored in the keyring.

        :param ks_entry: A list of two items, the keyring service [0] and
                         the account name [1].
        :type ks_entry: list
        """
        # Set correct UID and DBUS socket
        os.seteuid(self.uid)
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = self.bus

        pw = keyring.get_password(*ks_entry)
        """Reset to the original UID and BUS address.
        
        This might not be absolutely necessary, but doing it
        anyways, to make sure the changed environment doesn't
        affect other operations.
        """
        os.seteuid(BackupKeyring.runuser_id)
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = BackupKeyring.runuser_bus
        return pw
