# Copyright (C) 2019 Foundries.io
# Author: Andy Doan <andy@foundries.io>
import contextlib
import os

from pymysql import Connect

DB = os.environ.get('DEVICE_REGISTRY_DB', 'device_registry')
DBHOST = os.environ.get('DEVICE_REGISTRY_DBHOST', 'mysql')
DBUSER = os.environ.get('DEVICE_REGISTRY_DBUSER', 'device_registry')
DBPASS = os.environ.get('DEVICE_REGISTRY_DBPASS', 'device_registry')


@contextlib.contextmanager
def db_cursor(commit=False):
    con = None
    try:
        con = Connect(host=DBHOST, user=DBUSER, password=DBPASS, db=DB)
        with con.cursor() as cur:
            yield cur
        if commit:
            con.commit()
    finally:
        if con:
            con.close()


def migrate():
    stmt = '''
        CREATE TABLE IF NOT EXISTS OtaApiDeleted (
            uuid CHAR(36) NOT NULL,
            PRIMARY KEY (uuid)
        );
    '''
    with db_cursor() as c:
        c.execute(stmt)


def device_mark_deleted(device_uuid):
    '''Mark a device as deleted so that it won't ever be allowed to be added
       again.'''
    stmt = 'INSERT INTO OtaApiDeleted (uuid) VALUES (%s)'
    with db_cursor(commit=True) as c:
        c.execute(stmt, device_uuid)


def device_is_deleted(device_uuid):
    '''Check to see if this device was deleted. We can't allow it to be
       re-added and OTA connect will. Letting a device through will cause
       something like:
         https://github.com/advancedtelematic/ota-device-registry/issues/89
    '''
    stmt = '''SELECT uuid
              FROM OtaApiDeleted
              WHERE uuid = %s
           '''
    with db_cursor() as c:
        c.execute(stmt, device_uuid)
        for r in c:
            return True
