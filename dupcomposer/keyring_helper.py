import keyring
import os
import stat
import pwd

# The keyring user's id,
# or -1 if the same as the user running the backup (default)
uid = -1
# The socket address of the DBUS the Gnome Keyring
# is listening on.
bus_address = None


def init_backend():
    """Set the keyring backend to the GNOME keyring.

    If it is already set, leave it alone.
    """
    if not isinstance(keyring.get_keyring(),
                      keyring.backends.SecretService.Keyring):
        keyring.set_keyring(keyring.backends.SecretService.Keyring())


def set_special_env(username, socket_address):
    """Set a username and DBUS socket address different from the running user's environment.

    :param username: The name of the user "owning" the keyring.
    :type username: str
    :param socket_address: The file path to the DBUS socket, that should be
                           used to communicate with the keyring.
    :type socket_address: str
    """
    global uid
    global bus_address
    configured_uid = pwd.getpwnam(username).pw_uid
    # Storing the configured uid is not needed if we run
    # as the same euid, as we won't have to change the euid.
    if configured_uid != os.geteuid():
        uid = configured_uid
    mode = os.stat(socket_address).st_mode
    if stat.S_ISSOCK(mode) == False:
        raise OSError('Path %s is not a socket.' % socket_address)
    bus_address = socket_address


def get_secret(ks_entry):
    """Read from the keyring and return the secret string.

    The secret string can contain a password, passphrase or any string
    that is stored in the keyring.

    :param ks_entry: A list of two items, the keyring service [0] and
                     the account name [1].
    :type ks_entry: list
    """
    if uid != -1:
        os.seteuid(uid)
    if bus_address:
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = bus_address
    return keyring.get_password(*ks_entry)
