"""Function to get database information from env variables"""

import os
import boto3
import sqlalchemy


def get_engine(db_user_name, db_user_pass, db_host, db_name):
    """function to get database sqlalchemy engine"""

    db_url = f'mysql+pymysql://{db_user_name}:{db_user_pass}@{db_host}/{db_name}'
    engine = sqlalchemy.create_engine(db_url)
    return engine


def close_connections(engine):
    """function to close mysql connections"""
    engine.dispose()


def get_db_info():
    """function to get database info from environment"""

    DB_USER_NAME_SSM = os.environ.get('DB_USER_NAME_SSM')
    DB_USER_PASS_SSM = os.environ.get('DB_USER_PASS_SSM')
    DB_HOST_SSM = os.environ.get('DB_HOST_SSM')
    DB_NAME_SSM = os.environ.get('DB_NAME_SSM')
    REGION = os.environ.get('REGION', 'us-west-2')

    ssm = boto3.client('ssm', region_name=REGION)

    ssm_db_user_name = ssm.get_parameter(
        Name=DB_USER_NAME_SSM, WithDecryption=True
    )
    ssm_db_user_pass = ssm.get_parameter(
        Name=DB_USER_PASS_SSM, WithDecryption=True
    )
    ssm_db_host = ssm.get_parameter(
        Name=DB_HOST_SSM, WithDecryption=True
    )
    ssm_db_name = ssm.get_parameter(
        Name=DB_NAME_SSM, WithDecryption=True
    )

    DB_USER_NAME = ssm_db_user_name['Parameter']['Value']
    DB_USER_PASS = ssm_db_user_pass['Parameter']['Value']
    DB_HOST = ssm_db_host['Parameter']['Value']
    DB_NAME = ssm_db_name['Parameter']['Value']

    return DB_USER_NAME, DB_USER_PASS, DB_HOST, DB_NAME, REGION


def get_db_root_info():
    """function to get database root info from environment"""

    ROOT_USER_SSM = os.environ.get('ROOT_USER_SSM')
    ROOT_PASS_SSM = os.environ.get('ROOT_PASS_SSM')
    REGION = os.environ.get('REGION', 'us-west-2')

    ssm = boto3.client('ssm', region_name=REGION)

    ssm_db_root_user = ssm.get_parameter(
        Name=ROOT_USER_SSM, WithDecryption=True
    )
    ssm_db_root_pass = ssm.get_parameter(
        Name=ROOT_PASS_SSM, WithDecryption=True
    )

    DB_ROOT_USER = ssm_db_root_user['Parameter']['Value']
    DB_ROOT_PASS = ssm_db_root_pass['Parameter']['Value']

    return DB_ROOT_USER, DB_ROOT_PASS
