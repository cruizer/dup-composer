import unittest
import importlib
import os
import pwd
import uuid
import socket
from collections import namedtuple
import keyring
from keyring import backends
from unittest.mock import patch, Mock, MagicMock, call, DEFAULT
from dupcomposer import backup_keyring

class TestBackupKeyring(unittest.TestCase):

    
    @classmethod
    def setUpClass(cls):
        # Mock runner user  (whoever runs the tool)
        cls.dummy_runuser_id = 9003
        cls.dummy_runuser_bus = '/run/user/9003/bus'
        # Mock the user configured in the config file
        cls.config_username = 'mytestuser'
        cls.config_uid = 9000
        #
        # FILES
        #
        cls.temproot = '/tmp/'
        # Creating a plain file to test with
        cls.plain_file_path = cls.temproot + str(uuid.uuid4()) + '.regular_file'
        with open(cls.plain_file_path, 'w+') as f:
            pass
        # Creating a real socket file to test with
        cls.socket_path = cls.temproot + str(uuid.uuid4()) + '.socket_file'
        cls.test_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        cls.test_socket.bind(cls.socket_path)
        # This file shouldn't exist
        cls.dummy_path = cls.temproot + str(uuid.uuid4())



    @classmethod
    def tearDownClass(cls):
        cls.test_socket.close()
        try:
            os.remove(cls.socket_path)
        except OSError as ose:
            print('Could not tear down the test environment cleanly: %s' % ose)
        try:
            os.remove(cls.plain_file_path)
        except OSError as ose:
            print('Could not tear down the test environment cleanly: %s' % ose)


    @patch('os.geteuid')
    @patch('os.environ')
    @patch.multiple('keyring', get_keyring=DEFAULT, set_keyring=DEFAULT)
    def setUp(self, mock_env, mock_geteuid,
                   get_keyring, set_keyring):
        get_keyring.return_value = backends.SecretService.Keyring()
        mock_geteuid.return_value = self.dummy_runuser_id
        mock_env.get.return_value = self.dummy_runuser_bus
        importlib.reload(backup_keyring)


    @patch('os.geteuid')
    @patch('os.environ')
    @patch.multiple('keyring', get_keyring=DEFAULT, set_keyring=DEFAULT)
    def test_class_init(self, mock_env, mock_geteuid,
                        get_keyring, set_keyring):
        get_keyring.return_value = backends.chainer.ChainerBackend()
        mock_geteuid.return_value = self.dummy_runuser_id
        mock_env.get.return_value = self.dummy_runuser_bus
        importlib.reload(backup_keyring)
        self.assertTrue(isinstance(set_keyring.call_args[0][0],
                        backends.SecretService.Keyring))
        self.assertEqual(backup_keyring.BackupKeyring.runuser_id, self.dummy_runuser_id)
        self.assertEqual(backup_keyring.BackupKeyring.runuser_bus,self.dummy_runuser_bus)
        

    def test_instantiation_noconfig(self):
        kr = backup_keyring.BackupKeyring()
        self.assertEqual(kr.uid, self.dummy_runuser_id)
        self.assertEqual(kr.bus, self.dummy_runuser_bus)


    @patch('pwd.getpwnam')
    def test_instantiation_user_and_socket(self, getpwnam):
        getpwnam.return_value = Mock(pw_uid=self.config_uid)
        
        kr = backup_keyring.BackupKeyring(self.config_username, self.socket_path)

        self.assertEqual(kr.uid, self.config_uid)
        self.assertEqual(kr.bus, self.socket_path)

    def test_instantiation_socket_only(self):
        kr = backup_keyring.BackupKeyring(None, self.socket_path)

        self.assertEqual(kr.uid, self.dummy_runuser_id)
        self.assertEqual(kr.bus, self.socket_path)

    @patch('pwd.getpwnam')
    def test_instantiation_user_only_error(self, getpwnam):
        getpwnam.return_value = Mock(pw_uid=self.config_uid)
        self.assertRaises(ValueError,
                          backup_keyring.BackupKeyring,
                          self.config_username, None)

    @patch('pwd.getpwnam')
    def test_instantiation_no_such_user(self, getpwnam):
        getpwnam.side_effect = KeyError
        self.assertRaises(KeyError,
                          backup_keyring.BackupKeyring,
                          'nouser', self.socket_path)


    @patch('pwd.getpwnam')
    def test_instantiation_no_such_socket(self, getpwnam):
        getpwnam.return_value = Mock(pw_uid=self.config_uid)
        # Test for the path not existing
        self.assertRaises(FileNotFoundError,
                          backup_keyring.BackupKeyring,
                          self.config_username, self.dummy_path)
        # Test for the path not being a socket
        self.assertRaises(OSError,
                          backup_keyring.BackupKeyring,
                          self.config_username, self.plain_file_path)


    @patch('os.geteuid')
    @patch('os.environ')
    @patch.multiple('keyring', get_keyring=DEFAULT, set_keyring=DEFAULT)
    def test_instantiation_missing_bus_address(self, mock_env, mock_geteuid,
                        get_keyring, set_keyring):
        mock_geteuid.return_value = self.dummy_runuser_id
        mock_env.get.return_value = None
        importlib.reload(backup_keyring)
        self.assertRaises(ValueError,
                          backup_keyring.BackupKeyring)


    @patch('keyring.get_password')
    @patch('pwd.getpwnam')
    @patch.multiple('os', seteuid=DEFAULT, environ=DEFAULT)
    def test_get_secret(self, getpwnam, get_password,
                                              seteuid, environ):
        get_password.return_value = 'storedpassword'
        getpwnam.return_value = Mock(pw_uid=self.config_uid)
        kr = backup_keyring.BackupKeyring(self.config_username, self.socket_path)

        self.assertEqual(kr.get_secret(['service', 'account']),
                         'storedpassword')
        get_password.assert_called_once_with('service', 'account')
        self.assertEqual(seteuid.call_args_list,
                         [call(self.config_uid), call(self.dummy_runuser_id)])
        self.assertEqual(environ.__setitem__.call_args_list,
                         [call('DBUS_SESSION_BUS_ADDRESS', self.socket_path),
                          call('DBUS_SESSION_BUS_ADDRESS', self.dummy_runuser_bus)])
