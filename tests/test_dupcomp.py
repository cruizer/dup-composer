import unittest
from dupcomposer.backup_runner import read_config, BackupRunner
from dupcomposer.backup_config import BackupConfig

class TestBackupRunner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_data = read_config('tests/fixtures/dupcomposer-config.yml')
        cls.cmds_expected_bkup = \
            {'my_s3_backups': [['duplicity', '--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                '--volsize', '50',
                                '--file-prefix-archive', 'archive_',
                                '--file-prefix-manifest', 'manifest_',
                                '--file-prefix-signature', 'signature_',
                                '/home/shared',
                                's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/home/shared'],
                               ['duplicity', '--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                '--volsize', '50',
                                '--file-prefix-archive', 'archive_',
                                '--file-prefix-manifest', 'manifest_',
                                '--file-prefix-signature', 'signature_',
                                'etc',
                                's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/etc']],
             'my_s3_boto3_backups': [['duplicity', '--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                '--volsize', '50',
                                '--file-prefix-archive', 'archive_',
                                '--file-prefix-manifest', 'manifest_',
                                '--file-prefix-signature', 'signature_',
                                '/home/shared',
                                'boto3+s3://my-backup-bucket.s3.sa-east-1.amazonaws.com/home/shared'],
                               ['duplicity', '--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                '--volsize', '50',
                                '--file-prefix-archive', 'archive_',
                                '--file-prefix-manifest', 'manifest_',
                                '--file-prefix-signature', 'signature_',
                                'etc',
                                'boto3+s3://my-backup-bucket.s3.sa-east-1.amazonaws.com/etc']],
             'my_local_backups': [['duplicity', '--no-encryption', '--volsize', '200',
                                   '/var/www/html', 'file:///root/backups/var/www/html'],
                                  ['duplicity', '--no-encryption', '--volsize', '200',
                                   'home/tommy', 'file://backups/home/tommy']],
             'my_scp_backups': [['duplicity', '--no-encryption', '--volsize', '200',
                                 '/home/katy', 'scp://myscpuser@host.example.com//home/katy'],
                                ['duplicity', '--no-encryption', '--volsize', '200',
                                 'home/fun', 'scp://myscpuser@host.example.com/home/fun']]}

    def setUp(self):
        self.runner_backup_mode = BackupRunner(BackupConfig(self.config_data), 'backup')
        self.runner_restore_mode = BackupRunner(BackupConfig(self.config_data), 'restore')

    def test_instances(self):
        self.assertIsInstance(self.runner_backup_mode, BackupRunner)
        self.assertIsInstance(self.runner_restore_mode, BackupRunner)

    def test_invalid_mode(self):
        self.assertRaises(ValueError,
                          BackupRunner,
                          BackupConfig(self.config_data), 'foo')

    def test_invalid_config_object(self):
        self.assertRaises(ValueError,
                          BackupRunner,
                          {}, 'backup')
        
    def test_backup_get_cmds_raw(self):
       self.maxDiff = None
       self.assertEqual(self.runner_backup_mode.get_cmds_raw(),
                        self.cmds_expected_bkup)

    def test_backup_get_cmds_raw_specgroup(self):
        group_names = ['my_s3_backups', 'my_local_backups']
        data_expected = {}
        for name in group_names:
            data_expected[name] = self.cmds_expected_bkup[name]
        self.assertEqual(self.runner_backup_mode.get_cmds_raw(group_names),
                         data_expected)
