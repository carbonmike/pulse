#!/usr/bin/env python

'''
Usage:
    sms_console <configfile> --number <mobile_number>
    sms_console <configfile> --cmd <command_string>
'''


import os
from snap import snap, common
import docopt

import smslang as sms


def test_lexicon(command_lexicon):
    print(command_lexicon.compile_help_string())


def test_command_parsing(parser):

    #print(parser.parse_sms_message_body('Hlp'))
    #print(parser.parse_sms_message_body('on'))
    print(parser.parse_sms_message_body('$mymacro:help'))


def main(args):

    # Pulse subsystems:
    # scroll (SMS)
    # atrium (message routing/control)
    #   (web-aware front end)

    mobile_number = args['<mobile_number>']
    configfile = args['<configfile>']
    yaml_config = common.read_config_file(configfile)

    service_tbl = snap.initialize_services(yaml_config)
    registry = common.ServiceObjectRegistry(service_tbl)

    command_lexicon = sms.load_lexicon(yaml_config)
    parser = sms.SMSMessageParser(command_lexicon, '-')
    engine = sms.load_dialog_engine(yaml_config, command_lexicon, registry)

    if args['--cmd']:
        command_str = args['<command_string>']
        ctx = sms.SMSDialogContext(user=None, source_number=mobile_number, message=sms.unquote_plus(command_str))
        command = parser.parse_sms_message_body(command_str)
        response = engine.reply_command(command, ctx, command_lexicon, registry)
        print(f'\n{response}\n')

    else:
        while True:        
            sms_message = input('Enter a Pulse SMS command.\n>')
            ctx = sms.SMSDialogContext(user=None, source_number=mobile_number, message=sms.unquote_plus(sms_message))
            command = parser.parse_sms_message_body(sms_message)
            response = engine.reply_command(command, ctx, command_lexicon, registry)
            print(f'\n{response}\n')
        

if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)