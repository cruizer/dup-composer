# Dup-composer

Dup-composer is a front-end script for Duplicity, that lets you define your backups in a configuration file and execute them in a simple way.

**This is work in progress, hence it is not ready for production use yet.**

To get started:

- Download *Dup-composer*
- Create your YAML configuration file and define your backup groups configuration in this file.
- Execute `dupcomp.py`, define the groups you wish to execute and whether you want to do a `backup` or `restore`.

You can find more detail for each step in its respective section.

## Requirements - might change any time in the near future

- Duplicity 0.7 installed and the `duplicity` script on your PATH.
- Python 3.5
- PyYAML 5.1

## Download

A reasonable process of building and installing this tool into production is work in progress. Deploying from *PyPI* is the direction I am planning to take.

## Configuration

The configuration should follow [YAML 1.1](https://yaml.org/spec/1.1/) syntax.

Let's start at the top, with the list of backup groups - the three dots (...) are placeholders for child and scalar nodes:

```yaml
backup_groups:
  my_first_backup_group:
    ...
  my_second_backup_group:
    ...
```

The parent node of the groups is called `backup_groups`, which is currently the root of the configuration structure, but further configuration nodes might be added on the top level in the future.

### Backup group

For each backup group, you have to have the following structure in place:

```yaml
my_first_backup_group:
  encryption:
    ...
  backup_provider:
    ...    
  backup_file_prefixes:
    ...
  volume_size: ...
  sources:
    ...
```

The `encryption` node (mandatory) is the parent of the encryption related configuration, the children of `backup_provider`(mandatory) specify all the provider related properties. `backup_file_prefixes` is optional and contains the child nodes for archive, signature and manifest file prefix configuration. The `volumes_size` (mandatory) node determines the size of the backup archive file chunks in MBs.

### Encryption

There are primarily two ways to set up the `encryption` node at the moment.

Encryption is turned off:

```yaml
encryption:
  enabled: no
```

Encryption is turned on:

```yaml
encryption:
  enabled: yes
  gpg_key: 123456789ABCDEFF
  gpg_passphrase: examplepassphrase123
```

If the `enabled` node is set to `no`, encryption is disabled, there is no need to configure the `gpg-key` and `gpg-passphrase` nodes. When encryption is enabled however, they are mandatory. This key will be used both for signing and encrypting the backup data.

**Keyring support:** The value of `gpg_passphrase` can also be read from a keyring. See the [keyring support document](docs/md/keyring.md) for details.

### Backup provider

The `backup-provider` configuration to be configured largely depends on the type of the provider, determined by the URL scheme:

```yaml
backup-provider:
  url: file://
```

This configuration sets *Dup-composer* up to save the backup files on the **local filesystem**. There is no need to specify a concrete path here, as that will be determined by the `sources` section of the configuration. The URL will just set the *context* for those paths.

For a **remote SCP backup**, you need a slightly different configuration:

```yaml
backup-provider:
  url: scp://myscpuser@host.example.com/
  password: examplepassword123
```

In this case, you need to specify the username of the remote *SCP* host in the first part of the *SCP* URL, which is what you would do using *Duplicity* directly as well. Use the `password` node to specify the password.

**Keyring support:** The value of `password` can also be read from a keyring. See the [keyring support document](docs/md/keyring.md) for details.

Finally, you have to configure **AWS S3** like this:

```yaml
backup-provider:
  url: s3://s3.sa-east-1.amazonaws.com/my-backup-bucket
  aws_access_key: EXAMPLEACCESSKEY
  aws_secret_key: ExAmPlESeCrEtKeY
```

The S3 bucket URL is configured as the `url` node value, while `aws_access_key` and `aws_secret_key` need to contain your *AWS* generated keys for the bucket. Like with the rest of the providers, the actual path, folder, within the bucket shouldn't be added to the URL.

**Keyring support:** The value of `aws_secret_key` can also be read from a keyring. See the [keyring support document](docs/md/keyring.md) for details.

### Backup file prefixes

The next feature comes handy if you want to **prefix the generated backup file names** in a specific way. I use this to set up *bucket rules* in *S3*, that move my archive files to *Glacier*. Here is an example of the configuration:

```yaml
backup_file_prefixes:
  manifest: manifest_
  archive: archive_
  signature: signature_
```

The prefixes can be specifically set up for each file type generated at the backup location. Set these up as needed; you can leave the `backup_file_prefixes` node out altogether, if you don't need this feature.

### Volumes

The `volume-size` node is rather simple: a number should be given as its value; this determines the **archive size in megabytes**.

### Sources

Under the `sources` node in the configuration hierarchy, you can specify a **list of locations** (paths) you want to back up, where to back them up and where the restored data should go. You can set up multiple sources within a single group. Here is an example set of two sources configured:

```yaml
sources:
  /var/www/html:
    backup_path: /root/backups
    restore_path: /root/restored
  /home/tommy:
    backup_path: /home/bkup/my-laptop-backups
    restore_path: /root/restored-from-backup
```

The source child nodes `/var/www/html` and `/home/tommy` determine **the directory you want to back up**, and `backup_path` prescribes **the location the backup files will be saved to**. In practice, the value of `backup_path` will be appended to the value of the provider `url` node discussed earlier; hence these two fragments give the true backup location. `restore_path` is not used during the backup step, but specifying it is mandatory at the moment. I will remove this requirement very soon, as it doesn't make any sense, until an actual restore has to happen.

There are a few limitations on the path data provided in this configuration:
- They can't begin with a hyphen "-".
- They can't contain any backslash characters.
- They can't contain any newline characters.
- Extra: Make sure to check quoting rules if you need to add any characters, that have a special meaning in the *YAML* syntax.

### Example

`backup-compose.yml` example:

```yaml
backup_groups:
  my_local_backups:
    encryption:
      enabled: no
    backup_provider:
      url: file://
    volume_size: 200
    sources:
      /var/www/html:
        backup_path: /root/backups/var/www/html
        restore_path: /root/restored/var/www/html
      /home/tommy:
        backup_path: /root/backups/home/tommy
        restore_path: /root/restored/home/tommy
  my_s3_backups:
    encryption:
      enabled: yes
      gpg_key: xxxxxx
      gpg_passphrase: xxxxxx
    backup_provider:
      url: s3://s3.sa-east-1.amazonaws.com/my-backup-bucket
      aws_access_key: xxxxxx
      aws_secret_key: xxxxxx
    backup_file_prefixes:
      manifest: manifest_
      archive: archive_
      signature: signature_
    volume_size: 50
    sources:
      /etc:
        backup_path: /etc
        restore_path: /root/restored/etc
      /home/shared:
        backup_path: /home/shared
        restore_path: /root/restored/home/shared
  my_scp_backups:
    encryption:
      enabled: no
    backup_provider:
      url: scp://myscpuser@host.example.com/
      password: xxxxxx
    volume_size: 200
    sources:
      /home/fun:
        backup_path: /home/fun
        restore_path: /root/restored/home/fun
      /home/katy:
        backup_path: /home/katy
        restore_path: /root/restored/home/katy
```
## Usage

```bash
dupcomp.py [-d] [-c <configpath>] backup|restore [backup_group1 backup_group2 ...]
```
