import unittest
import subprocess
import os
import json

class TestCLI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_data = {
            'backup_example_complete':
                     {'config_file': 'dupcomposer-config.yml',
                      'command': ['python3', 'dupcomp.py', 'backup'],
                      'result': [['--no-encryption', '--volsize', '200', '/var/www/html',
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
                                  'scp://myscpuser@host.example.com/home/fun']]}
        }
        cls.dummy_outfile = 'tests/temp/dummy-out.json'

    def setUp(self):
        pass

    def tearDown(self):
        os.remove(self.dummy_outfile)

    def test_simple(self):
        os.putenv('PATH', ':'.join(['./tests/mock', os.getenv('PATH')]))
        subprocess.run(self.test_data['backup_example_complete']['command'])
        with open(self.dummy_outfile) as f:
            result = json.loads(f.read())
        self.assertEqual(result, self.test_data['backup_example_complete']['result'])
