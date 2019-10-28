import unittest
import importlib
import os
import uuid
import socket
from collections import namedtuple
from keyring.backends import SecretService, chainer
from unittest.mock import patch, Mock
from dupcomposer import keyring_helper

class TestKeyringHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
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


    def setUp(self):
        # Force reload module to reset config
        # module variables after each test.
        importlib.reload(keyring_helper)


    @patch('dupcomposer.keyring_helper.keyring',
           spec=['set_keyring', 'get_keyring', 'backends'])
    def test_init_backend_sameuser_gnomedefault(self, mock_keyring):
        mock_keyring.get_keyring.return_value = SecretService.Keyring()
        mock_keyring.backends.SecretService = SecretService

        keyring_helper.init_backend()

        mock_keyring.get_keyring.assert_called_once()
        mock_keyring.set_keyring.assert_not_called()
        self.assertEqual(keyring_helper.uid, -1)


    @patch('dupcomposer.keyring_helper.keyring',
           spec=['set_keyring', 'get_keyring', 'backends'])
    def test_init_backend_sameuser_notgnomedefault(self, mock_keyring):
        mock_keyring.get_keyring.return_value = chainer.ChainerBackend()
        mock_keyring.backends.SecretService.Keyring = SecretService.Keyring

        keyring_helper.init_backend()

        mock_keyring.get_keyring.assert_called_once()
        mock_keyring.set_keyring.assert_called_once()
        self.assertTrue(isinstance(mock_keyring.set_keyring.call_args[0][0],
                                   SecretService.Keyring))
        self.assertEqual(keyring_helper.uid, -1)

    @patch('dupcomposer.keyring_helper.pwd', spec=['getpwnam'])
    def test_set_special_environment(self, mock_pwd):
        PwdEntry = namedtuple('test_pwd_entry', ['pw_name', 'pw_passwd',
                                                 'pw_uid', 'pw_gid',
                                                 'pw_gecos', 'pw_dir',
                                                 'pw_shell'])
        mock_pwd.getpwnam.return_value = PwdEntry('testuser', 'x', 9000, 9000,
                                                  ',,,', '/home/testuser',
                                                  '/bin/bash')
        keyring_helper.set_special_env('testuser', self.socket_path)
        self.assertEqual(keyring_helper.uid, 9000)
        self.assertEqual(keyring_helper.bus_address, self.socket_path)


    @patch('dupcomposer.keyring_helper.pwd', spec=['getpwnam'])
    def test_special_environment_nosuchuser(self, mock_pwd):
        mock_pwd.getpwnam.side_effect = KeyError
        self.assertRaises(KeyError,
                          keyring_helper.set_special_env,
                          'nouser', self.socket_path)

    @patch('dupcomposer.keyring_helper.os.geteuid')
    @patch('dupcomposer.keyring_helper.pwd', spec=['getpwnam'])
    def test_special_evironment_sameuser(self, mock_pwd, mock_geteuid):
        mock_pwd.getpwnam.return_value = Mock(pw_uid=9000)
        mock_geteuid.return_value = 9000
        keyring_helper.set_special_env('testuser', self.socket_path)
        self.assertEqual(keyring_helper.uid, -1)

    @patch('dupcomposer.keyring_helper.pwd', spec=['getpwnam'])
    def test_special_environment_nosuchsocket(self, mock_pwd):
        mock_pwd.getpwnam.return_value = Mock(pw_uid=9000)
        # Test for the path not existing
        self.assertRaises(FileNotFoundError,
                          keyring_helper.set_special_env,
                          'myuser', self.dummy_path)
        # Test for the path not being a socket
        self.assertRaises(OSError,
                          keyring_helper.set_special_env,
                          'myuser', self.plain_file_path)


    @patch('dupcomposer.keyring_helper.keyring', spec=['get_password'])
    @patch('dupcomposer.keyring_helper.os', spec=['seteuid', 'environ'])
    def test_get_secret(self, mock_os, mock_keyring):
        mock_keyring.get_password.return_value = 'mysecret'
        mock_os.environ = {'DBUS_SESSION_BUS_ADDRESS': 'dummycheckval'}

        self.assertEqual(keyring_helper.get_secret(['service', 'account']),
                         'mysecret')
        mock_keyring.get_password.assert_called_once_with('service', 'account')
        # Make sure the environment is not changed in the deafault case.
        mock_os.seteuid.assert_not_called()
        self.assertEqual(mock_os.environ['DBUS_SESSION_BUS_ADDRESS'],
                         'dummycheckval')



    @patch('dupcomposer.keyring_helper.keyring', spec=['get_password'])
    @patch('dupcomposer.keyring_helper.os', spec=['seteuid', 'environ'])
    def test_get_secret_with_special_env(self, mock_os, mock_keyring):
        # Use runner user keyring with custom socket config
        keyring_helper.uid = -1
        keyring_helper.bus_address = '/custom/bus/address'
        mock_os.environ = {'DBUS_SESSION_BUS_ADDRESS': 'dummycheckval'}
        keyring_helper.get_secret(['service', 'account'])
        mock_os.seteuid.assert_not_called()
        self.assertEqual(mock_os.environ['DBUS_SESSION_BUS_ADDRESS'],
                         keyring_helper.bus_address)
        # Use a different user's keyring
        keyring_helper.uid = 9000
        keyring_helper.bus_address = '/run/user/9000/bus2'
        mock_os.environ = {'DBUS_SESSION_BUS_ADDRESS': 'dummycheckval'}
        keyring_helper.get_secret(['service', 'account'])
        mock_os.seteuid.assert_called_with(9000)
        self.assertEqual(mock_os.environ['DBUS_SESSION_BUS_ADDRESS'],
                         keyring_helper.bus_address)
