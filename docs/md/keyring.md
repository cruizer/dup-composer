# Keyring integration for dup-composer credentials

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
### Starting GNOME Keyring in an interactive DBUS session

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

In this step you need to provide the passphrase the GNOME Keyring is locked with, then press *Ctrl+D*. On the first launch, the keyring is automatically initialized and it will be locked with the passphrase you provide the first time. **Make sure to take a note of the passphrase after the first use as you will need it to unlock the same keyring in the future.**

After this is done, you can run your backup with Dup-composer, the utility will read secrets from the keyring as configured.

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

### Running GNOME Keyring detached from the user login session

If you want to run scheduled backups with *Dup-composer*, which should also run if the user is not logged in, the methods detailed above won't work. There are some further, more elaborate steps needed to create a GNOME Keyring instance, that:

- Is available even if there is no user logged in.
- Remains unlocked all the time.

### Add the user that will own the keyring

In case you don't want to store the backup secrets in the keyring of the *root* user for organization purposes, or for other reasons, you can also use the keyring of another user. Probably the best way is to create a user, that is dedicated to own your backup keyring exclusively:

```
# adduser backupkeyringuser
```

### Enable user linger

The systemd user instance and the user's services are normally started when the user logs in. However, since we want *gnome-keyring-daemon* to run at all times, we have to enable user linger, so that the user's services are started on boot instead.

```
# loginctl enable-linger backupkeyringuser
```

### Create the service unit file for gnome-keyring-daemon

First of all, log in as the user that will be the keyring owner and create the directory, where the user's unit files will be placed:

```
$ mkdir -p ~/.config/systemd/user
```

Create a markdown unit file in this directory, give it some meaningful name, like *gnome-keyring.service*. Here is an example of the possible content that works:

```
[Unit]
Description=Backup Keyring

[Service]
Type=forking
StandardInput=file:/home/backupkeyringuser/.keyring_pp
ExecStart=/usr/bin/gnome-keyring-daemon --unlock -d
Restart=on-failure

[Install]
WantedBy=default.target
```
#### Create the input file for the keyring passphrase

As you can see in the unit file above, the `StandardInput` of the service is a file at the path:

```
/home/backupkeyringuser/.keyring_pp
```

This is the file used to store the keyring passphrase, that is used to encrypt the keyring when it is persisted and to decrypt (unlock) it when it is opened. The first time GNOME Keyring is started it automatically initializes the keyring.

Before moving on, add your, preferably randomly generated, passphrase string to this file.

#### Set the DBUS_SESSION_BUS_ADDRESS in .bashrc (optional)

The user's session bus address is set through PAM when you do a proper console login. However, since this user will be just just used to own and manage the keyring, you might just want to simply `su - backupkeyringuser` in your primary user's terminal session and in that case, ther user's bus address won't be set automatically, so you need to do it manually, or otherwise you won't be able to use the `systemctl --user` command line or the `keyring` utility, as they won't know the *D-Bus* socket they need to connect to.

If you want set it up for once and for all, you can add this snippet to the `.bashrc` file of *backupkeyringuser*:

```bash
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
fi
```

The D-Bus address will be automatically set the next time you change to this user, make sure to use *su* with the hyphen option, that loads the user's environment as well.
