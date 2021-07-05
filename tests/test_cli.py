import unittest
from unittest.mock import patch
import subprocess
import os
import shutil
import filecmp
import glob
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
        terminal_encoding = os.environ['LANG'].split('.')[1].lower()
        path_raw = subprocess.run(['which', 'python3'],
                                  stdout=subprocess.PIPE).stdout
        cls.py3_exec = path_raw.decode(terminal_encoding).strip()
        cls.test_data = {
            'backup_example_complete':
                     {'config_file': 'dupcomposer-config.yml',
                      'command': [cls.py3_exec, cls.console_script, 'backup'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '/var/www/html',
                                  'file:///root/backups/var/www/html'],
                                 ['--no-encryption', '--volsize', '200', 'home/tommy',
                                  'file://backups/home/tommy'],
                                 ['--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                  '--volsize', '50', '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  '/home/shared',
                                  's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/home/shared'],
                                 ['--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx', '--volsize', '50',
                                  '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  'etc', 's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/etc'],
                                  ['--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                  '--volsize', '50', '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  '/home/shared',
                                  'boto3+s3://my-backup-bucket.s3.sa-east-1.amazonaws.com/home/shared'],
                                 ['--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx', '--volsize', '50',
                                  '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  'etc', 'boto3+s3://my-backup-bucket.s3.sa-east-1.amazonaws.com/etc'],
                                  ['--no-encryption', '--volsize', '200', '/home/katy',
                                  'scp://myscpuser@host.example.com//home/katy'],
                                 ['--no-encryption', '--volsize', '200', 'home/fun',
                                  'scp://myscpuser@host.example.com/home/fun']],
                                 'envs': [{},
                                          {},
                                          {'AWS_ACCESS_KEY_ID': 'xxxxxx', 'AWS_SECRET_ACCESS_KEY': 'xxxxxx'},
                                          {'AWS_ACCESS_KEY_ID': 'xxxxxx', 'AWS_SECRET_ACCESS_KEY': 'xxxxxx'},
                                          {'AWS_ACCESS_KEY_ID': 'xxxxxx', 'AWS_SECRET_ACCESS_KEY': 'xxxxxx'},
                                          {'AWS_ACCESS_KEY_ID': 'xxxxxx', 'AWS_SECRET_ACCESS_KEY': 'xxxxxx'},
                                          {'FTP_PASSWORD': 'xxxxxx'},
                                          {'FTP_PASSWORD': 'xxxxxx'}]}},
            'backup_example_specgroups':
                     {'config_file': 'dupcomposer-config.yml',
                      'command': [cls.py3_exec, cls.console_script,
                                  'backup', 'my_local_backups', 'my_s3_backups'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '/var/www/html',
                                   'file:///root/backups/var/www/html'],
                                  ['--no-encryption', '--volsize', '200', 'home/tommy',
                                   'file://backups/home/tommy'],
                                  ['--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                   '--volsize', '50', '--file-prefix-archive', 'archive_',
                                   '--file-prefix-manifest', 'manifest_',
                                   '--file-prefix-signature', 'signature_',
                                   '/home/shared',
                                   's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/home/shared'],
                                 ['--encrypt-key', 'xxxxxx', '--sign-key', 'xxxxxx',
                                  '--volsize', '50',
                                  '--file-prefix-archive', 'archive_',
                                  '--file-prefix-manifest', 'manifest_',
                                  '--file-prefix-signature', 'signature_',
                                  'etc', 's3://s3.sa-east-1.amazonaws.com/my-backup-bucket/etc']],
                                 'envs':
                                 [{},
                                  {},
                                  {'AWS_ACCESS_KEY_ID': 'xxxxxx', 'AWS_SECRET_ACCESS_KEY': 'xxxxxx'},
                                  {'AWS_ACCESS_KEY_ID': 'xxxxxx', 'AWS_SECRET_ACCESS_KEY': 'xxxxxx'}]}
                     },
            'backup_scpurl_fix':
                     {'config_file': 'dupcomposer-config-scpurl.yml',
                      'command': [cls.py3_exec, cls.console_script, '-c',
                                  'dupcomposer-config-scpurl.yml', 'backup'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '/var/www/html',
                                   'scp://user@myhost.example.com//home/bkup']],
                                 'envs': [{'FTP_PASSWORD': 'yyyyyy'}]}},
            'backup_sftp':
                     {'config_file': 'dupcomposer-config-sftp.yml',
                      'command': [cls.py3_exec, cls.console_script, '-c',
                                  'dupcomposer-config-sftp.yml', 'backup'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '/var/www/html',
                                   'sftp://sftpuser@myhost.example.com//home/bkup']],
                                 'envs': [{'FTP_PASSWORD': 'xxxxxx'}]}},
            'backup_filters':
                     {'config_file': 'dupcomposer-config-filters.yml',
                      'command': [cls.py3_exec, cls.console_script, '-c',
                                  'dupcomposer-config-filters.yml', 'backup'],
                      'result': {'args':
                                 [['--no-encryption', '--volsize', '200', '--exclude',
                                   '/dummyusr/secrets', '--include', '/dummyusr/pub',
                                   '/dummyusr', 'file:///backups/dummyusr']],
                                 'envs': [{}]
                                 }
                      },
            'backup_filters_restore':
                      {'config_file': 'dupcomposer-config-filters.yml',
                       'command': [cls.py3_exec, cls.console_script, '-c',
                                   'dupcomposer-config-filters.yml', 'restore'],
                       'result': {'args':
                                  [['--no-encryption', '--volsize', '200',
                                    'file:///backups/dummyusr', '/root/restore/dummyusr']],
                                  'envs': [{}]
                                  }
                       },
            'backup_full':
                       {'config_file': 'dupcomposer-config-2.yml',
                        'command': [cls.py3_exec, cls.console_script, '-f',
                                    '-c', 'dupcomposer-config-2.yml', 'backup',
                                    'groupone'],
                        'result': {'args':
                                   [['full', '--no-encryption', '--volsize', '500',
                                     '/etc', 'file:///root/backups/system'],
                                    ['full', '--no-encryption', '--volsize', '500',
                                     '/home/foo/bar', 'file:///root/backups/user']],
                                   'envs': [{}, {}]
                                   }
                        },
            'full_frequency_backup':
                        {'config_file': 'dupcomposer-config-full-frequency.yml',
                         'command': [cls.py3_exec, cls.console_script, '-c',
                                     'dupcomposer-config-full-frequency.yml', 'backup'],
                         'result': {'args':
                                    [['--no-encryption', '--volsize', '486',
                                      '--full-if-older-than', '1M', '/var/foo',
                                      'file:///foo/backup']],
                                    'envs': [{}]
                                    }
                         },
            'full_frequency_restore':
                        {'config_file': 'dupcomposer-config-full-frequency.yml',
                         'command': [cls.py3_exec, cls.console_script, '-c',
                                     'dupcomposer-config-full-frequency.yml', 'restore'],
                         'result': {'args':
                                    [['--no-encryption', '--volsize', '486',
                                      'file:///foo/backup', '/foo/restore']],
                                    'envs': [{}]
                                    }
                         }
        }
        #cls.dummy_outfile = '../temp/dummy-out.json'
        cls.dummy_outfile = '/tmp/' + str(uuid.uuid4()) + '.json'
        cls.environ = os.environ.copy()
        # We share the generated outfile with the mock
        cls.environ['duplicity_mock_outfile'] = cls.dummy_outfile
        # Update path, so the mock Duplicity implementation is called.
        cls.environ['PATH'] = ':'.join(['../mock', os.environ['PATH']])


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
        # clean up any existing cache files generated
        for filename in glob.glob('*.cached'):
            os.remove(filename)


    def test_simple(self):
        self.maxDiff = None
        self.assertEqual(self._get_duplicity_results('backup_example_complete'),
                         self.test_data['backup_example_complete']['result'])

    def test_specific_groups(self):
        self.maxDiff = None
        self.assertEqual(self._get_duplicity_results('backup_example_specgroups'),
                         self.test_data['backup_example_specgroups']['result'])

    def test_scp_missing_trailing_backslash(self):
        self.assertEqual(self._get_duplicity_results('backup_scpurl_fix'),
                         self.test_data['backup_scpurl_fix']['result'])
    def test_sftp(self):
        self.assertEqual(self._get_duplicity_results('backup_sftp'),
                         self.test_data['backup_sftp']['result'])

    def test_full_frequency_backup(self):
        self.assertEqual(self._get_duplicity_results('full_frequency_backup'),
                         self.test_data['full_frequency_backup']['result'])


    def test_full_frequency_restore(self):
        self.assertEqual(self._get_duplicity_results('full_frequency_restore'),
                         self.test_data['full_frequency_restore']['result'])


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
                    'Generating commands for group my_s3_boto3_backups:\n\n'
                    'duplicity --encrypt-key xxxxxx --sign-key xxxxxx '
                    '--volsize 50 --file-prefix-archive archive_ '
                    '--file-prefix-manifest manifest_ '
                    '--file-prefix-signature signature_ '
                    '/home/shared boto3+s3://my-backup-bucket.s3.sa-east-1.amazonaws.com/home/shared\n'
                    'duplicity --encrypt-key xxxxxx --sign-key xxxxxx '
                    '--volsize 50 --file-prefix-archive archive_ '
                    '--file-prefix-manifest manifest_ '
                    '--file-prefix-signature signature_ '
                    'etc boto3+s3://my-backup-bucket.s3.sa-east-1.amazonaws.com/etc\n\n'
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


    def test_invalid_missing_action(self):
        expected = r'^backup\|restore action is missing'
        self.assertRegex(self._get_cmd_out(['-c', 'dupcomposer-config.yml']),
                         expected)
        self.assertRegex(self._get_cmd_out(['-c', 'dupcomposer-config.yml', 'foo']),
                         expected)

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


    def test_duplicity_not_found(self):
        with patch.dict(self.environ, {'PATH': ''}):
            self.assertRegex(self._get_cmd_out(['backup']),
                             r'^duplicity executable not found')


    def test_duplicity_oldversion(self):
        with patch.dict(self.environ, {'PATH': '../mock/old-version'}):
            self.assertRegex(self._get_cmd_out(['backup']),
                             r'^Unsupported Duplicity version 0\.4\.1')


    def test_duplicity_nonzero_return(self):
        with patch.dict(self.environ, {'PATH': '../mock/versioncheck-failed'}):
            self.assertRegex(self._get_cmd_out(['backup']),
                             r'^Executing "duplicity --version" has failed')

        with patch.dict(self.environ, {'PATH': '../mock/nonzero-returncode'}):
            self.assertEqual(self._get_cmd_returncode(['backup']),
                             42)

    def test_changed_config(self):
        self.assertRegex(self._get_cmd_out(['-c', 'cache-test-fixture/dupcomposer-config-changed.yml', 'backup']),
                         r'^The configuration of existing group\(s\) '
                         'backup_local, backup_server')
    def test_invalid_option_full_for_restore(self):
        self.assertRegex(self._get_cmd_out(['-f', '-c', 'dupcomposer-config.yml', 'restore']),
                         r'^-f: force full backup is an invalid option')


    def test_changed_config_skip(self):
        expected = ('Generating commands for group backup_local:\n\n'
                    'duplicity --no-encryption --volsize 200 '
                    '/home/shared file:///home/shared\n'
                    'duplicity --no-encryption --volsize 200 '
                    'etc file://etc'
                    '\n\n'
                    'Generating commands for group backup_server:\n\n'
                    'duplicity --no-encryption --volsize 200 '
                    '/var/www/html sftp://sshuser@backuphost.example.com//root/backups/var/www/html'
                    '\n\n'
                    'Generating commands for group unchanged_group:\n\n'
                    'duplicity --no-encryption --volsize 200 '
                    '/etc file:///home/backups/etc\n\n')
        # We have to  test with dry run, so that our test
        # cache file is not updated!
        self.assertEqual(self._get_cmd_out(['-s', '-d', '-c',
                                            'cache-test-fixture/dupcomposer-config-changed.yml',
                                            'backup']),
                         expected)

    def test_cache_file_create(self):
        dummyfile = '/tmp/' + str(uuid.uuid4()) + '.yml'
        cachefile = '.'.join([dummyfile, '.cached'])
        shutil.copyfile('cache-test-fixture/dupcomposer-config-changed.yml', dummyfile)
        self._get_cmd_out(['-c', dummyfile, 'backup'])
        self.assertTrue(filecmp.cmp(dummyfile, cachefile))
        os.remove(dummyfile)
        os.remove(cachefile)

    def test_filters_backup(self):
        self.assertEqual(self._get_duplicity_results('backup_filters'),
                         self.test_data['backup_filters']['result'])

    def test_filters_not_present_at_restore(self):
        self.assertEqual(self._get_duplicity_results('backup_filters_restore'),
                         self.test_data['backup_filters_restore']['result'])

    def test_force_full_backup(self):
        self.assertEqual(self._get_duplicity_results('backup_full'),
                         self.test_data['backup_full']['result'])


    # END test methods
    # START utility methods
    def _run_cmd(self, args):
        """Execute dupcomp with the provided args and return the output."""
        cmd = [self.py3_exec, self.console_script]
        cmd.extend(args)
        proc = subprocess.Popen(cmd, universal_newlines=True,
                                env=self.environ,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        return proc

    def _get_cmd_out(self, args):
        """Execute dupcomp with the provided args and return the output."""
        proc = self._run_cmd(args)
        return proc.communicate()[0]

    def _get_cmd_returncode(self, args):
        proc = self._run_cmd(args)
        proc.communicate()
        return proc.returncode

    def _get_duplicity_results(self, test_data_variant):
        subprocess.run(self.test_data[test_data_variant]['command'],
                       env=self.environ)
        with open(self.dummy_outfile) as f:
            result = json.loads(f.read())
        return result
