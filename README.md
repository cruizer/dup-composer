# duplicity-compose
Simple configuration wrapper for Duplicity

## Configuration

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
