# duplicity-compose
Simple configuration wrapper for Duplicity

## Configuration

`backup-compose.yml` example:

```yaml
backup_groups:
  my_local_backups:
    encrypted: no
    backup_type: local
    volume_size: 200
    origins:
      /var/www/html:
        backup_path: /root/backups/var/www/html
        restore_path: /root/restored/var/www/html
      /home/tommy:
        backup_path: /root/backups/home/tommy
        restore_path: /root/restored/home/tommy
  my_s3_backups:
    encrypted: yes
    backup_type: s3
    backup_uri: s3://s3.sa-east-1.amazonaws.com/my-backup-bucket
    aws_access_key: xxxxxx
    aws_secret_key: xxxxxx
    gpg_key: xxxxxx
    gpg_passphrase: xxxxxx
    volume_size: 50
    origins:
      /etc:
        backup_path: /etc
        restore_path: /root/restored/etc
      /home/shared:
        backup_path: /home/shared
        restore_path: /root/restored/home/shared
  my_scp_backups:
    encrypted: no
    backup_type: scp
    backup_uri: scp://myscpuser@host.example.com/
    volume_size: 200
    origins:
      /home/fun:
        backup_path: /home/fun
        restore_path: /root/restored/home/fun
      /home/katy:
        backup_path: /home/katy
        restore_path: /root/restored/home/katy
```
## Usage

```bash
duplicity-compose.py backup_group1[/origin1/origin2/...] command
```
