# Keyring integration for dup-composer credential

## Supported configuration properties

Currently, you can have *Dup-composer* read the following credentials from the keyring:

- GPG passphrases
- SCP passwords
- S3 secret keys

## Keyring interoperability

*Dup-composer* uses the Python [keyring](https://pypi.org/project/keyring/) library to interface with various keyring backends. Since the library API abstracts the backend implementations, you should be able to use all the ones supported by *keyring* as long as you take care of the backend being accessible.

The *Dup-composer* recommended backend to use is [GNOME Keyring](https://wiki.gnome.org/Projects/GnomeKeyring), so additional help and documentation is provided to set it up (see below).

The following dependency versions should work with *Dup-composer* as of now:

- keyring 19.2.0
- SecretStorage 3.1.1

## Using Dup-composer with GNOME keyring in a GUI session

If you are using the GNOME Desktop environment, it is very likely, that the keyring is running in the background unlocked. In this case, you can use your favorite GNOME Keyring frontend GUI application, eg. *Seahorse*, to create the entries for the secrets you want to store and have Dup-composer read from the keyring.

As long as you execute Dup-composer from within the GNOME Desktop Environment, it should be able to read the configured secrets from the keyring.

## Using Dup-composer with GNOME Keyring on a headless Linux server

In order to use Dup-composer with GNOME Keyring *interactively*, there are a few additional steps you need to take to make it work.

First of all, it is very likely, that GNOME Keyring is not installed by default.

To install on Debian 10 (buster), run:

```
# apt update
# apt install gnome-keyring
```

To install on Red Hat / CentOS 8, run:

```
# yum install gnome-keyring
```

GNOME Keyring uses DBUS for communication, so Dup-composer has to have access to the DBUS session bus to communicate with the keyring. The official Python *keyring* library documentation [shows how to start](https://pypi.org/project/keyring/#using-keyring-on-headless-linux-systems) a DBUS session bus and GNOME Keyring instance interactively, but you can also see the steps below.

Start the DBUS session:

```
# dbus-run-session -- sh
```

This command will start the DBUS session and drop you into a shell environment with the `DBUS_SESSION_BUS_ADDRESS` environment variable set. Both *GNOME Keyring* and the Python *keyring* library will connect to the socket specified by this environment variable, hence they will be able to communicate with each other over the bus listening on this socket.

Start the GNOME Keyring:

```
# gnome-keyring-daemon --unlock
```

In this step you need to provide the passphrase the GNOME Keyring is locked with, then press *Ctrl+D*. On the first launch, the keyring is automatically initialized and it will be locked with passphrase you provide the first time. **Make sure to take a note of the passphrase after the first use as you will need it to unlock the same keyring in the future.**

After this is done, you can run your backup with Dup-composer, that will read secrets from the keyring as configured.

### Adding your secrets to the keyring

Before Dup-composer can read passwords, passphrases and other secrets from the keyring, you have to add those to the keyring. The easiest way to do this, is to use the Python *keyring* command line utility:

```
# keyring -b keyring.backends.SecretService.Keyring set AWS backupu
```

The command above will set the password of the *backupu* user of the *AWS* service.

**NOTE:** If the *SecretService* backend is the default one in your environment, you can omit the `-b` option altogether. You can verify your default (highest priority) backend, by running `keyring --list-backends`. The default keyring backend can also be set in the [configuration file](https://pypi.org/project/keyring/#customize-your-keyring-by-config-file).

You can verify, that the information above was indeed added to the keyring, by running:

```
# keyring -b keyring.backends.SecretService.Keyring get AWS backupu
```

### Starting your backup

Once the environment has been set up and the credentials to be used by *Dup-composer* were added to the keyring, you just have to execute the backup as you normally would.

### Closing the session

Once the backup is complete, you can close the DBUS session with:

```
# exit
```

Remember: You have to have the *DBUS session* and *gnome-keyring-daemon* running, before starting your backup or restore. Start it again before running *Dup-composer* again.