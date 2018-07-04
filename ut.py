#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Unittest for setsts.py '''

import datetime

import unittest

try:
    from unittest.mock import MagicMock
except ImportError:
    # Python 2
    from mock import MagicMock


import setsts


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
