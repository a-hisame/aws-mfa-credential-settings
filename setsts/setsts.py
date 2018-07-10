#!/usr/bin/python
# -*- coding: utf-8 -*-

''' STS Token inject into your aws profile '''

import sys
import os
import shutil
import codecs
import argparse

if sys.version_info.major == 3:
    from configparser import ConfigParser
elif sys.version_info.major == 2:
    from StringIO import StringIO
    from ConfigParser import ConfigParser
else:
    raise RuntimeError('no supported python version')

import boto3


def _get_virtual_mfa_serial_number(sts):
    res = sts.get_caller_identity()
    return res['Arn'].replace(':user/', ':mfa/')


def _get_serial_number(sts, serial_number):
    if serial_number is not None:
        return serial_number
    return _get_virtual_mfa_serial_number(sts)


def _get_aws_credential_filepath(aws_credential_filepath):
    if aws_credential_filepath is not None:
        return aws_credential_filepath
    home = os.path.expanduser('~')
    return os.environ.get('AWS_CREDENTIAL_FILE',
                          os.path.join(home, '.aws/credentials'))


def _get_temporary_credentials(sts, serial_number, duration_seconds, token_code):
    res = sts.get_session_token(
        DurationSeconds=duration_seconds,
        SerialNumber=serial_number, TokenCode=token_code)
    return res.get('Credentials')


def _create_new_credential_parser(config_contents, profile, access_key, secret_access_key, session_token):
    parser = ConfigParser()
    if sys.version_info.major == 3:
        parser.read_string(config_contents)
    else:
        parser.readfp(StringIO(config_contents))

    if not parser.has_section(profile):
        parser.add_section(profile)
    parser.set(profile, 'aws_access_key_id', access_key)
    parser.set(profile, 'aws_secret_access_key', secret_access_key)
    parser.set(profile, 'aws_session_token', session_token)
    return parser


def _console_factory(is_quiet):
    def _console(message, force=False):
        if all([is_quiet, not force]):
            return
        print(message)
    return _console


def _save_credentials(configfile, parser, console,
                      dryrun=False, ignore_backup=False):
    def _dryrun_wrapper(msg, func):
        if dryrun:
            console('> dryrun: {msg}'.format(msg=msg))
        else:
            func()

    if not ignore_backup:
        backuppath = configfile + '~'
        _dryrun_wrapper('create backup file',
                        lambda: shutil.copy(configfile, backuppath))
        console('> created backup file: ' + backuppath)

    def _save():
        with codecs.open(configfile, 'w') as fh:
            parser.write(fh)
    _dryrun_wrapper('override credential file', _save)


def _main(args):
    sts = boto3.session.Session(profile_name=args.profile).client('sts')
    serial_number = _get_serial_number(sts, args.serial_number)
    configfile = _get_aws_credential_filepath(args.aws_credential_file)

    console = _console_factory(args.quiet)
    console('AWS STS Credential Setup')
    console('> credential filepath: ' + configfile)
    console('> serial number: ' + serial_number)

    try:
        credential = _get_temporary_credentials(
            sts, serial_number, args.duration_seconds, args.token_code)
        console('> created temporary credential succeeded')
        console('> expired datetime: ' + str(credential['Expiration']))
    except Exception as e:
        console('> failed: create temporary credential - ' + str(e), force=True)
        console('aborted.', force=True)
        return 1

    with codecs.open(configfile, 'r') as fh:
        console('> output target profile: ' + args.target_profile)
        parser = _create_new_credential_parser(
            fh.read(), args.target_profile,
            credential['AccessKeyId'], credential['SecretAccessKey'],
            credential['SessionToken'])

    _save_credentials(
        configfile, parser, console,
        dryrun=args.dryrun, ignore_backup=args.ignore_backup)

    console('completed!')
    return 0


def _parse_args(argv=sys.argv[1:]):
    ''' parse program arguments by argparse module '''
    parser = argparse.ArgumentParser(
        description='create AWS session token and set them into your AWS credential file',
        add_help=True)
    parser.add_argument('--profile', required=False,
                        help='MFA configured AWS profile (if not set, use default)')
    parser.add_argument('--serial-number', required=False,
                        help="MFA device serial number.  you don't have to input it, if you use virtual device")
    parser.add_argument('--token-code', required=True,
                        help='MFA digit code')
    parser.add_argument('--duration-seconds', default=43200, type=int,
                        help='Session token duration seconds, default is 12 hours (43200). Between 900 and 129600')
    parser.add_argument('--target-profile', required=True,
                        help='Configuration target profile name (override if exists)')
    parser.add_argument('--aws-credential-file',
                        help='AWS credential file specific setting (if no input, choose automatically)')
    parser.add_argument('--ignore-backup', action='store_true',
                        help='ignore backup copy before override configuration file (name: with ~ suffix)')
    parser.add_argument('--quiet', action='store_true',
                        help='no stdout mode (but when message shown if error occurred)')
    parser.add_argument('--dryrun', action='store_true',
                        help='run the program without any modifications')
    return parser.parse_args(argv)


def main(argv=sys.argv[1:]):
    _main(_parse_args(argv))


if __name__ == '__main__':
    exitcode = _main(_parse_args())
    sys.exit(exitcode)
