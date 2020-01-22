import unittest
import subprocess
import os
import json
import uuid

class TestCLI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Pretend that tests/fixtures is the directory
        # dupcomp.py was called from.
        cls.workdir_original = os.getcwd()
        os.chdir('./tests/fixtures')
        cls.console_script = '../../dupcomp'
        cls.test_data = {
            'backup_example_complete':
                     {'config_file': 'dupcomposer-config.yml',
                      'command': ['python3', cls.console_script, 'backup'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '/var/www/html',
                                  'file:///root/backups/var/www/html'],
                                 ['--no-encryption', '--volsize', '200', 'home/tommy',
                                  'file://backups/home/tommy'],
                                 ['--encrypt-key xxxxxx', '--sign-key xxxxxx',
                                  '--volsize', '50', '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  '/home/shared',
                                  's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/home/shared'],
                                 ['--encrypt-key xxxxxx', '--sign-key xxxxxx', '--volsize', '50',
                                  '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  'etc', 's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/etc'],
                                 ['--no-encryption', '--volsize', '200', '/home/katy',
                                  'scp://myscpuser@host.example.com//home/katy'],
                                 ['--no-encryption', '--volsize', '200', 'home/fun',
                                  'scp://myscpuser@host.example.com/home/fun']],
                                 'envs': [{},
                                          {},
                                          {'AWS_ACCESS_KEY': 'xxxxxx', 'AWS_SECRET_KEY': 'xxxxxx'},
                                          {'AWS_ACCESS_KEY': 'xxxxxx', 'AWS_SECRET_KEY': 'xxxxxx'},
                                          {'FTP_PASSWORD': 'xxxxxx'},
                                          {'FTP_PASSWORD': 'xxxxxx'}]}},
            'backup_example_specgroups':
                     {'config_file': 'dupcomposer-config.yml',
                      'command': ['python3', cls.console_script,
                                  'backup', 'my_local_backups', 'my_s3_backups'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '/var/www/html',
                                   'file:///root/backups/var/www/html'],
                                  ['--no-encryption', '--volsize', '200', 'home/tommy',
                                   'file://backups/home/tommy'],
                                  ['--encrypt-key xxxxxx', '--sign-key xxxxxx',
                                   '--volsize', '50', '--file-prefix-archive', 'archive_',
                                   '--file-prefix-manifest', 'manifest_',
                                   '--file-prefix-signature', 'signature_',
                                   '/home/shared',
                                   's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/home/shared'],
                                 ['--encrypt-key xxxxxx', '--sign-key xxxxxx', '--volsize', '50',
                                  '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  'etc', 's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/etc']],
                                 'envs':
                                 [{},
                                  {},
                                  {'AWS_ACCESS_KEY': 'xxxxxx', 'AWS_SECRET_KEY': 'xxxxxx'},
                                  {'AWS_ACCESS_KEY': 'xxxxxx', 'AWS_SECRET_KEY': 'xxxxxx'}]}},
            'backup_scpurl_fix':
                     {'config_file': 'dupcomposer-config-scpurl.yml',
                      'command': ['python3', cls.console_script, '-c',
                                  'dupcomposer-config-scpurl.yml', 'backup'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '/var/www/html',
                                   'scp://user@myhost.example.com//home/bkup']],
                                 'envs': [{'FTP_PASSWORD': 'yyyyyy'}]}}
        }
        #cls.dummy_outfile = '../temp/dummy-out.json'
        cls.dummy_outfile = '/tmp/' + str(uuid.uuid4()) + '.json'
        # We share the generated outfile with the mock
        os.environ['duplicity_mock_outfile'] = cls.dummy_outfile
        # Update path, so the mock Duplicity implementation is called.
        os.environ['PATH'] = ':'.join(['../mock', os.environ['PATH']])


    @classmethod
    def tearDownClass(cls):
        # Reset workdir after we are done with the CLI tests.
        os.chdir(cls.workdir_original)

    def setUp(self):
        pass

    def tearDown(self):
        try:
            os.remove(self.dummy_outfile)
        except FileNotFoundError:
            pass

    def test_simple(self):
        self.assertEqual(self._get_duplicity_results('backup_example_complete'),
                         self.test_data['backup_example_complete']['result'])


    def test_specific_groups(self):
        self.assertEqual(self._get_duplicity_results('backup_example_specgroups'),
                         self.test_data['backup_example_complete']['result'])

    def test_scp_missing_trailing_backslash(self):
        self.assertEqual(self._get_duplicity_results('backup_scpurl_fix'),
                         self.test_data['backup_scpurl_fix']['result'])

    def test_dry(self):
        expected = ('Generating commands for group my_local_backups:\n\n'
                    'duplicity --no-encryption --volsize 200 /var/www/html '
                    'file:///root/backups/var/www/html\n'
                    'duplicity --no-encryption --volsize 200 home/tommy '
                    'file://backups/home/tommy\n\n'
                    'Generating commands for group my_s3_backups:\n\n'
                    'duplicity --encrypt-key xxxxxx --sign-key xxxxxx '
                    '--volsize 50 --file-prefix-archive archive_ '
                    '--file-prefix-manifest manifest_ '
                    '--file-prefix-signature signature_ '
                    '/home/shared s3://s3.sa-east-1.amazonaws.com/my-backup-bucket/home/shared\n'
                    'duplicity --encrypt-key xxxxxx --sign-key xxxxxx '
                    '--volsize 50 --file-prefix-archive archive_ '
                    '--file-prefix-manifest manifest_ '
                    '--file-prefix-signature signature_ '
                    'etc s3://s3.sa-east-1.amazonaws.com/my-backup-bucket/etc\n\n'
                    'Generating commands for group my_scp_backups:\n\n'
                    'duplicity --no-encryption --volsize 200 /home/katy '
                    'scp://myscpuser@host.example.com//home/katy\n'
                    'duplicity --no-encryption --volsize 200 home/fun '
                    'scp://myscpuser@host.example.com/home/fun\n\n')

        self.assertEqual(self._get_cmd_out(['-d', 'backup']),
                         expected)

    def test_dry_specific_groups(self):
        expected = ('Generating commands for group my_s3_backups:\n\n'
                    'duplicity --encrypt-key xxxxxx --sign-key xxxxxx '
                    '--volsize 50 --file-prefix-archive archive_ '
                    '--file-prefix-manifest manifest_ '
                    '--file-prefix-signature signature_ '
                    '/home/shared s3://s3.sa-east-1.amazonaws.com/my-backup-bucket/home/shared\n'
                    'duplicity --encrypt-key xxxxxx --sign-key xxxxxx '
                    '--volsize 50 --file-prefix-archive archive_ '
                    '--file-prefix-manifest manifest_ '
                    '--file-prefix-signature signature_ '
                    'etc s3://s3.sa-east-1.amazonaws.com/my-backup-bucket/etc\n\n'
                    'Generating commands for group my_scp_backups:\n\n'
                    'duplicity --no-encryption --volsize 200 /home/katy '
                    'scp://myscpuser@host.example.com//home/katy\n'
                    'duplicity --no-encryption --volsize 200 home/fun '
                    'scp://myscpuser@host.example.com/home/fun\n\n')

        self.assertEqual(self._get_cmd_out(['-d', 'backup',
                                            'my_s3_backups',
                                            'my_scp_backups']),
                         expected)

    def test_dry_scp_missing_trailing_backslash(self):
        expected = ('Generating commands for group scp_backup:\n\n'
                    'duplicity --no-encryption --volsize 200 '
                    '/var/www/html '
                    'scp://user@myhost.example.com//home/bkup\n\n')

        self.assertEqual(self._get_cmd_out(['-d', '-c',
                                            'dupcomposer-config-scpurl.yml',
                                            'backup']),
                         expected)

    def test_invalid_option(self):
        self.assertRegex(self._get_cmd_out(['-c', 'foo.bar', '-a', 'backup']),
                         r'^option -a not recognized')

    def test_invalid_group(self):
        self.assertRegex(self._get_cmd_out(['backup', 'foo']),
                         r'ValueError: No group foo in the configuration!')

    def test_specific_config_file(self):
       expected = ('Generating commands for group groupone:\n\n'
                   'duplicity --no-encryption --volsize 500 '
                   '/etc file:///root/backups/system\n'
                   'duplicity --no-encryption --volsize 500 '
                   '/home/foo/bar file:///root/backups/user\n\n'
                   'Generating commands for group grouptwo:\n\n'
                   'duplicity --encrypt-key yyyyyy --sign-key yyyyyy --volsize 200 '
                   '/var/lib scp://myuser@host.example2.com//root/backups/system/libs\n\n')
       self.assertEqual(self._get_cmd_out(['-d', '-c',
                                           './dupcomposer-config-2.yml',
                                           'backup']),
                        expected)

    # END test methods
    # START utility methods

    def _get_cmd_out(self, args):
        """Execute dupcomp with the provided args and return the output."""
        cmd = ['python3', self.console_script]
        cmd.extend(args)
        proc = subprocess.Popen(cmd, universal_newlines=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.communicate()[0]

    def _get_duplicity_results(self, test_data_variant):
        subprocess.run(self.test_data[test_data_variant]['command'])
        with open(self.dummy_outfile) as f:
            result = json.loads(f.read())
        return result
