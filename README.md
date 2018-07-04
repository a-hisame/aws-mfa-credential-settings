# AWS STS Credential Settings

When you use IAM access key tied with MFA user and managed strictly policies
[(i.e. policy denies any AWS API call except MFA certification)] (https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_users-self-manage-mfa-and-creds.html),
you have to publish session token by `get-session-token` and use it.

The API returns `access_key` , `secret_access_key` and `session_token`
but you also have to set them into aws credential configuration,
especially you use them by `awscli` .

This project objective is to provide easy way to use created sts temporary credential.

## Precondition

1. MFA is activated on your IAM user and the user is allowed to call following APIs.
2. You set access_key and secret_access_key of the user into credential file (like `aws configure` command)

* sts:GetCallerIdentity
* sts:GetSessionToken

see: https://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html


## Environment

I tested following Python version by virtualenv on ubuntu.

* Python 2.7.15rc
* Python 3.6.5

```
pip install awscli boto3
```

## How to Use

Download `setsts.py` file and run following command as minimum usage.

```
python setsts.py \
    --profile <MFA IAM user profile> \
    --target-profile <profile name what you want to set> \
    --token-code <current MFA token code>
```

Program outputs like following messages (several lines are masked).

```
$ python setsts.py --profile a-hisame --target-profile temporary --token-code XYZXYZ
AWS STS Credential Setup
> credential filepath: /home/ubuntu/.aws/credentials
> serial number: arn:aws:iam::************:mfa/a-hisame
> created temporary credential succeeded
> expired datetime: 2018-07-04 05:46:53+00:00
> created backup file: /home/ubuntu/.aws/credentials~
> output target profile: temporary
completed!
```

After succeeded, you can use MFA certificated `temporary` profile.

```
# MFA is not certificated so failed
$ aws s3 ls --profile a-hisame

An error occurred (AccessDenied) when calling the ListBuckets operation: Access Denied

# works well to use MFA certificated profile
$ aws s3 ls --profile temporary
2017-09-27 22:16:18 ......
```


### Options and Specifications

You can know detailed specifications by `--help` option.

```
$ python setsts.py --help
usage: setsts.py [-h] [--profile PROFILE] [--serial-number SERIAL_NUMBER]
                 --token-code TOKEN_CODE [--duration-seconds DURATION_SECONDS]
                 --target-profile TARGET_PROFILE
                 [--aws-credential-file AWS_CREDENTIAL_FILE] [--ignore-backup]
                 [--quiet]

create AWS session token and set them into your AWS credential file

optional arguments:
  -h, --help            show this help message and exit
  --profile PROFILE     MFA configured AWS profile (if not set, use default)
  --serial-number SERIAL_NUMBER
                        MFA device serial number. you don't have to input it,
                        if you use virtual device
  --token-code TOKEN_CODE
                        MFA digit code
  --duration-seconds DURATION_SECONDS
                        Session token duration seconds, default is 12 hours
                        (43200). Between 900 and 129600
  --target-profile TARGET_PROFILE
                        Configuration target profile name (override if exists)
  --aws-credential-file AWS_CREDENTIAL_FILE
                        AWS credential file specific setting (if no input,
                        choose automatically)
  --ignore-backup       ignore backup copy before override configuration file
                        (name: with ~ suffix)
  --quiet               no stdout mode (but when message shown if error
                        occurred)
```


## Notice

* This program sets only aws credential settings.
  If you want to set default `region` and `output` on AWS configuration file,
  You run `aws configure --profile [target profile]` and set them
  (You can skip access keys with empty input).
* This program overrides aws credential file.
  To avoid wrong operation such as override and delete another credentials,
  it provides backup creation before to override current configuration.
  But author never guarantee any trouble by using this project even if it has the critical bugs.


## License

* [MIT License](LICENSE)
