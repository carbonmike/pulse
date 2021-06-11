#!/usr/bin/env python


'''
Usage:
    mkuser --dbconfig <configfile> --name <username> --email <email> --pk-uri <public_key_uri> [--params=<name:value>...]
'''


import os, sys
import json
from snap import common
import docopt

def generate_temp_password():
    return 'ch4ng3-me-1st'


def main(args):
    username = args['<username>']
    email_addr = args['<email>']
    temp_password = generate_temp_password()



if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)

    

