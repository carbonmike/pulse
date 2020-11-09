#!/usr/bin/env python

'''
Usage:
    sms_console <configfile>
'''


import os
from snap import snap, common
import docopt

import smslang as sms

def main(args):

    configfile = args['<configfile>']
    yaml_config = common.read_config_file(configfile)

    service_tbl = snap.initialize_services(yaml_config)
    registry = common.ServiceObjectRegistry(service_tbl)
    command_lexicon = sms.load_lexicon(yaml_config)

    #print(command_lexicon.compile_help_string())

    parser = sms.SMSMessageParser(command_lexicon, '-')
    print(parser.parse_sms_message_body('Hlp'))
    #print(parser.parse_sms_message_body('on'))

    print(parser.parse_sms_message_body('$mymacro:help'))


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)