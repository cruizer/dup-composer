import unittest
from dupcomposer.dupcomposer import read_config

class TestReadConfig(unittest.TestCase):

    def test_load_goodfile(self):
        config = read_config('tests/fixtures/dupcomposer-config.yml')
        self.assertEqual(config['backup_groups']['my_s3_backups']['volume_size'], 50)

    def test_load_filenotfound(self):
        self.assertRaises(FileNotFoundError,
                          read_config,
                          'tests/fixtures/dupcomposer-notfound.yml')

if __name__ == '__main__':
    unittest.main()
