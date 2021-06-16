#!/usr/bin/env python


'''
Usage:
    mkuser --dbconfig <configfile> --name <username> --email <email> --pk-uri <public_key_uri> [--params=<name:value>...]
'''


import os, sys
import json
import uuid
import datetime
from snap import snap, common
import docopt

def generate_temp_password():
    return 'ch4ng3-me-1st'


class ObjectFactory(object):
    @classmethod
    def create_pulse_user(cls, db_svc, **kwargs):
        User = db_svc.Base.classes.users
        return User(**kwargs)


def generate_uuid():
    newid = uuid.uuid4()
    return str(newid)


def now():
    return datetime.datetime.now()


def main(args):

    configfile = args['<configfile>']
    yaml_config = common.read_config_file(configfile)
    service_registry = common.ServiceObjectRegistry(snap.initialize_services(yaml_config))

    username = args['<username>']
    email_addr = args['<email>']
    temp_password = generate_temp_password()

    db_svc = service_registry.lookup('postgres')
    with db_svc.txn_scope() as session:
        new_user = ObjectFactory.create_pulse_user(db_svc, **{
            'id': generate_uuid(),
            'username': username,
            'password': temp_password,
            'email': email_addr,
            'sms_country_code': '1',
            'sms_phone_number': '9174176968',
            'status': 1,
            'created_ts': now()
        })

        session.add(new_user)


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)

    

