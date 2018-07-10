#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Unittest for setsts.py '''
import sys
import datetime

import unittest

if sys.version_info.major == 3:
    from unittest.mock import MagicMock, patch, mock_open
elif sys.version_info.major == 2:
    from mock import MagicMock, patch, mock_open
else:
    raise RuntimeError('no supported python version')

from nose.tools import eq_, ok_
from botocore.exceptions import ClientError

from setsts import setsts


class TestSetSTS(unittest.TestCase):
    def _create_mock_sts(self):
        m = MagicMock()
        m.get_caller_identity = MagicMock(return_value={
            'Account': '123456789012',
            'Arn': 'arn:aws:sts::123456789012:user/my-role-name',
            'UserId': 'AKIAI44QH8DHBEXAMPLE:my-role-name',
        })
        m.get_session_token = MagicMock(return_value={
            'Credentials': {
                'AccessKeyId': 'AKIAIOSFODNN7EXAMPLE',
                'Expiration': datetime.datetime(2018, 7, 4),
                'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY',
                'SessionToken': 'EXAMPLESESSION',
            }
        })
        return m

    def test_files_got_modification(self):
        sts = self._create_mock_sts()
        backupcopy = MagicMock()
        mockio = mock_open()
        with patch('boto3.session.Session.client', return_value=sts), \
                patch('shutil.copy', backupcopy), \
                patch('codecs.open', mockio):
            setsts.main([
                '--token-code', 'XYZXYZ',
                '--target-profile', 'tmpcode',
            ])

        # copy backup and override credential file
        ok_(backupcopy.called)
        fh = mockio()
        expecteds = [
            '[tmpcode]',
            'aws_access_key_id = AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY',
            'aws_session_token = EXAMPLESESSION',
            ''
        ]
        actuals = [args[0] for (args, kwargs) in fh.write.call_args_list]
        for (expected, actual) in zip(expecteds, actuals):
            ok_(expected in actual)

    def test_files_with_dryrun(self):
        sts = self._create_mock_sts()
        backupcopy = MagicMock()
        mockio = mock_open()
        with patch('boto3.session.Session.client', return_value=sts), \
                patch('shutil.copy', backupcopy), \
                patch('codecs.open', mockio):
            setsts.main([
                '--aws-credential-file', 'hogehoge',
                '--token-code', 'XYZXYZ',
                '--target-profile', 'tmpcode',
                '--dryrun', '--ignore-backup', '--quiet'
            ])
        # never copy and write
        ok_(not backupcopy.called)
        ok_(not mockio().write.called)

    def test_if_get_credential_failed(self):
        sts = self._create_mock_sts()
        sts.get_session_token = MagicMock(
            side_effect=ClientError({}, 'GetSessionToken'))
        with patch('boto3.session.Session.client', return_value=sts), \
                patch('shutil.copy', MagicMock()), \
                patch('codecs.open', mock_open(read_data='')):
            setsts.main([
                '--token-code', 'XYZXYZ',
                '--target-profile', 'tmpcode',
            ])

    def test_serial_number(self):
        sts = self._create_mock_sts()
        self.assertEqual(
            'arn:aws:sts::123456789012:mfa/my-role-name',
            setsts._get_serial_number(sts, None))
        self.assertEqual(
            'DEVICE00000',
            setsts._get_serial_number(sts, 'DEVICE00000'))

    def test_credential_file(self):
        parser1 = setsts._create_new_credential_parser(
            '', 'test', 'AAA', 'BBB', 'CCC')
        self.assertEqual(parser1.get('test', 'aws_access_key_id'), 'AAA')
        self.assertEqual(parser1.get('test', 'aws_secret_access_key'), 'BBB')
        self.assertEqual(parser1.get('test', 'aws_session_token'), 'CCC')

        # override
        base2 = '\n'.join([
            '[test]',
            'aws_access_key_id = aaa',
            'aws_secret_access_key = bbb',
            'aws_session_token = ccc',
        ])
        parser2 = setsts._create_new_credential_parser(
            base2, 'test', 'AAA2', 'BBB2', 'CCC2')
        self.assertEqual(parser2.get('test', 'aws_access_key_id'), 'AAA2')
        self.assertEqual(parser2.get('test', 'aws_secret_access_key'), 'BBB2')
        self.assertEqual(parser2.get('test', 'aws_session_token'), 'CCC2')

        base3 = '\n'.join([
            '[test]',
            'aws_access_key_id = aaa',
            'aws_secret_access_key = bbb',
            'aws_session_token = ccc',
            '',
            '[test2]',
            'aws_access_key_id = ddd',
            'aws_secret_access_key = eee',
            'aws_session_token = fff',
        ])
        parser3 = setsts._create_new_credential_parser(
            base3, 'test', 'AAA3', 'BBB3', 'CCC3')
        self.assertEqual(parser3.get('test', 'aws_access_key_id'), 'AAA3')
        self.assertEqual(parser3.get('test', 'aws_secret_access_key'), 'BBB3')
        self.assertEqual(parser3.get('test', 'aws_session_token'), 'CCC3')
        self.assertEqual(parser3.get('test2', 'aws_access_key_id'), 'ddd')
        self.assertEqual(parser3.get('test2', 'aws_secret_access_key'), 'eee')
        self.assertEqual(parser3.get('test2', 'aws_session_token'), 'fff')


if __name__ == '__main__':
    unittest.main()
