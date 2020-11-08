#!/usr/bin/env python

'''
SMS command definition and handling logic

containing patterns and structures adapted from open-source code donated by @binarymachines (Thank You) 
'''


import os, sys
import json
import re
import uuid
import json
import traceback
import datetime
from collections import namedtuple
from urllib.parse import unquote_plus

from pulse_sms_services import SMSService

from snap import common

SMSCommandSpec = namedtuple('SMSCommandSpec', 'command definition synonyms tag_required')
SMSGeneratorSpec = namedtuple('SMSGeneratorSpec', 'command definition specifier filterchar')
SMSPrefixSpec = namedtuple('SMSPrefixSpec', 'command definition defchar')

SystemCommand = namedtuple('SystemCommand', 'job_tag cmdspec modifiers')
GeneratorCommand = namedtuple('GeneratorCommand', 'cmd_string cmdspec modifiers')
PrefixCommand = namedtuple('PrefixCommand', 'mode name body cmdspec')
CommandInput = namedtuple('CommandInput', 'cmd_type cmd_object')  # command types: generator, syscommand, prefix

SMSDialogContext = namedtuple('SMSDialogContext', 'user source_number message')


SMS_SYSTEM_COMMAND_SPECS = {
    'on': SMSCommandSpec(command='on', definition='Courier coming on duty', synonyms=[], tag_required=False),
    'off': SMSCommandSpec(command='off', definition='Courier going off duty', synonyms=[], tag_required=False),
    'bid': SMSCommandSpec(command='bid', definition='Bid for a delivery job', synonyms=[], tag_required=True),
    'acc': SMSCommandSpec(command='acc', definition='Accept a delivery job', synonyms=['ac'], tag_required=True),
    'dt': SMSCommandSpec(command='dt', definition='Detail (find out what a particular job entails)', synonyms=[], tag_required=True),
    'ert': SMSCommandSpec(command='ert', definition='En route to either pick up or deliver for a job', synonyms=['er'], tag_required=True),
    'can': SMSCommandSpec(command='can', definition='Cancel (courier can no longer complete an accepted job)', synonyms=[], tag_required=True),
    'mdel': SMSCommandSpec(command='mdel', definition='Delete a user message', synonyms=[], tag_required=False),
    'fin': SMSCommandSpec(command='fin', definition='Finished a delivery', synonyms=['f'], tag_required=True),
    '911': SMSCommandSpec(command='911', definition='Courier is having a problem and needs assistance', synonyms=[], tag_required=False),
    'hlp': SMSCommandSpec(command='hlp', definition='Display help prompts', synonyms=['?'], tag_required=False)
}

SMS_GENERATOR_COMMAND_SPECS = {
    'my': SMSGeneratorSpec(command='my', definition='List my pending (already accepted) jobs', specifier='.', filterchar='?'),
    'opn': SMSGeneratorSpec(command='opn', definition='List open (available) jobs', specifier='.', filterchar='?'),
    'awd': SMSGeneratorSpec(command='awd', definition='List my awarded (but not yet accepted) jobs', specifier='.', filterchar='?'),
    'prg': SMSGeneratorSpec(command='prg', definition='List jobs in progress', specifier='.', filterchar='?'),
    'msg': SMSGeneratorSpec(command='msg', definition='Display messages belonging to user', specifier='.', filterchar='?'),
    'bst': SMSGeneratorSpec(command='bst', definition='Bidding status (jobs you have bid on)', specifier='.', filterchar='?')
}


SMS_PREFIX_COMMAND_SPECS = {
    '$': SMSPrefixSpec(command='$', definition='create a user-defined macro', defchar=':'),
    '@': SMSPrefixSpec(command='@', definition="send a message to a user's log via his or her handle", defchar=' '),
    '&': SMSPrefixSpec(command='&', definition='create a user handle for yourself', defchar=' '),
    '#': SMSPrefixSpec(command='#', definition='look up an abbreviation', defchar=':')
}

class UnrecognizedSMSCommand(Exception):
    def __init__(self, cmd_string):
        super().__init__(self, 'Invalid SMS command %s' % cmd_string)


class IncompletePrefixCommand(Exception):
    def __init__(self, cmd_string):
        super().__init__(self, 'Incomplete prefix command %s' % cmd_string)


def normalize_mobile_number(number_string):
    return number_string.lstrip('+').lstrip('1').replace('(', '').replace(')', '').replace('-', '').replace('.', '').replace(' ', '')


def ok_status(message, **kwargs):
    result = {
        'status': 'ok',
        'message': message
    }

    if kwargs:
        result['data'] = kwargs

    return json.dumps(result)


def exception_status(err, **kwargs):
    result = {
        'status': 'error',
        'error_type': err.__class__.__name__,
        'message': 'an exception of type %s occurred: %s' % (err.__class__.__name__, str(err))
    }

    if kwargs:
        result.update(**kwargs)

    return json.dumps(result)


class CommandLexicon(object):
    def __init__(self):
        self.system_commands = {}
        self.generator_commands = {}
        self.prefix_commands = {}
        self.command_macros = {}

    def register_sys_command_spec(self, cmdspec: SMSCommandSpec):
        self.system_commands[cmdspec.command] = cmdspec
        

    def register_gen_command_spec(self, cmdspec: SMSGeneratorSpec):
        self.generator_commands[cmdspec.command] = cmdspec


    def register_pfx_command_spec(self, cmdspec: SMSPrefixSpec):
        self.prefix_commands[cmdspec.command] = cmdspec

    def register_command_macro_spec(self):
        pass


    def lookup_sms_command(self, cmd_string):
        for key, cmd_spec in self.system_commands.items():
            if cmd_string == key:
                return cmd_spec
            if cmd_string in cmd_spec.synonyms:
                return cmd_spec

        return None


    def lookup_generator_command(self, cmd_string):
        for key, cmd_spec in self.generator_commands.items():
            delimiter = cmd_spec.specifier
            filter_char = cmd_spec.filterchar

            print('the filter character is [%s].' % filter_char)

            if cmd_string.split(delimiter)[0] == key:
                return cmd_spec

            if cmd_string.split(filter_char)[0] == key:
                return cmd_spec

        return None

    def lookup_macro(self, courier_id, macro_name, session, db_svc):
        pass


    def compile_help_string(self):
        lines = []

        lines.append('________')

        lines.append('[ SYSTEM commands ]:')
        for key, cmd_spec in self.system_commands.items():
            lines.append('%s : %s' % (key, cmd_spec.definition))
        
        lines.append('________')

        lines.append('[ LISTING commands ]:')
        for key, cmd_spec in self.generator_commands.items():
            lines.append('%s : %s' % (key, cmd_spec.definition))
        
        lines.append('________')

        lines.append('[ PREFIX commands ]:')
        for key, cmd_spec in self.prefix_commands.items():
            lines.append('%s : %s' % (key, cmd_spec.definition))

        lines.append('________')

        return '\n\n'.join(lines)


class SMSCommandDispatcher(object):
    def __init__(self):
        pass

    def call_system_command(self, cmd_object, dlg_context, service_registry, **kwargs):
        pass

    def call_generator_command(self, cmd_object, dlg_engine, dlg_context, service_registry, **kwargs):
        pass


class SMSMessageParser(object):
    def __init__(self, lexicon:CommandLexicon, prefix_separator: str):
        self.lexicon = lexicon
        self.prefix_separator = prefix_separator
        self.systemdata_prefix_handlers = {}


    def register_sysdata_prefix_handler(self, prefix_string, handler_function):
        self.systemdata_prefix_handlers[prefix_string] = handler_function


    def parse_sms_message_body(self, raw_body:str):
        job_tag = None
        command_string = None
        modifiers = []

        # make sure there's no leading whitespace, then see what we've got
        body = unquote_plus(raw_body).lstrip().rstrip().lower()

        print('\n\n###__________ inside parse logic. Raw message body is:')
        print(body)
        print('###__________\n\n')

        body_prefix = body.split(self.prefix_separator)[0]
        prefix_handler = self.systemdata_prefix_handlers.get(body_prefix)
        if prefix_handler:

            # remove the URL encoded whitespace chars;
            # remove any trailing/leading space chars as well
            tokens = [token.lstrip().rstrip() for token in body.split(' ') if token]

            #print('###------ message tokens: %s' % common.jsonpretty(tokens))

            job_tag = tokens[0]
            if len(tokens) == 2:
                command_string = tokens[1].lower()

            if len(tokens) > 2:
                command_string = tokens[1].lower()
                modifiers = tokens[2:]

            print('#--------- looking up system SMS command: %s...' % command_string)
            command_spec = self.lexicon.lookup_sms_command(command_string)
            if command_spec:
                return CommandInput(cmd_type='syscommand', cmd_object=SystemCommand(job_tag=job_tag,
                                                                                    cmdspec=command_spec,
                                                                                    modifiers=modifiers))
            raise UnrecognizedSMSCommand(command_string)

        elif body[0] in SMS_PREFIX_COMMAND_SPECS.keys():
            prefix = body[0]
            prefix_spec = SMS_PREFIX_COMMAND_SPECS[prefix]
            print('### probable prefix command "%s". Body length is %d.' % (prefix, len(body)))
            if len(body) == 1:
                raise IncompletePrefixCommand(command_string)

            raw_body = body[1:].lower()
            defchar_index = raw_body.find(prefix_spec.defchar)
            # when a prefix command is issued containing a defchar, that is its "extended" mode
            if defchar_index > 0:            
                command_mode = 'extended'
                command_name = raw_body[0:defchar_index]
                command_data = raw_body[defchar_index+1:]
            # prefix commands issued without the defchar are running in "simple" mode
            else:
                command_mode = 'simple'
                command_name = raw_body
                command_data = None

            return CommandInput(cmd_type='prefix',
                                cmd_object=PrefixCommand(mode=command_mode,
                                                        name=command_name,
                                                        body=command_data,
                                                        cmdspec=prefix_spec))

        else:
            tokens = [token.lstrip().rstrip() for token in body.split(' ') if token]
            command_string = tokens[0].lower()
            modifiers = tokens[1:]

            # see if we received a generator 
            # (a command which generates a list or a slice of a list)

            print('******************* LOOKING UP GENERATOR CMD for string [%s]...' % command_string)
            command_spec = lookup_generator_command(command_string)
            if command_spec:
                print('###------------ detected GENERATOR-type command: %s' % command_string)            
                return CommandInput(cmd_type='generator',
                                    cmd_object=GeneratorCommand(cmd_string=command_string,
                                                                cmdspec=command_spec,
                                                                modifiers=modifiers))

            # if we didn't find a generator, perhaps the user issued a regular sms comand                                             
            command_spec = lookup_sms_command(command_string)
            if command_spec:
                print('###------------ detected system command: %s' % command_string)
                return CommandInput(cmd_type='syscommand',
                                    cmd_object=SystemCommand(job_tag=job_tag,
                                                            cmdspec=command_spec,
                                                            modifiers=modifiers))
        
            raise UnrecognizedSMSCommand(command_string)


class DialogEngine(object):
    def __init__(self):
        self.msg_dispatch_tbl = {}
        self.generator_dispatch_tbl = {}
        self.prefix_dispatch_tbl = {}


    def register_cmd_spec(self, sms_command_spec, handler_func):
        self.msg_dispatch_tbl[str(sms_command_spec)] = handler_func

    def register_generator_cmd(self, generator_cmd_spec, handler_func):
        self.generator_dispatch_tbl[str(generator_cmd_spec)] = handler_func

    def register_prefix_cmd(self, prefix_spec, handler_func):
        self.prefix_dispatch_tbl[str(prefix_spec)] = handler_func


    def _reply_prefix_command(self, prefix_cmd, dialog_context, service_registry, **kwargs):
        command = self.prefix_dispatch_tbl.get(str(prefix_cmd.cmdspec))
        if not command:
            return 'No handler registered in SMS DialogEngine for prefix command %s.' % prefix_cmd.cmdspec.command
        return command(prefix_cmd, self, dialog_context, service_registry)


    def _reply_generator_command(self, gen_cmd, dialog_context, service_registry, **kwargs):
        list_generator = self.generator_dispatch_tbl.get(str(gen_cmd.cmdspec))
        if not list_generator:
            return 'No handler registered in SMS DialogEngine for generator command %s.' % gen_cmd.cmdspec.command
        return list_generator(gen_cmd, self, dialog_context, service_registry)


    def _reply_sys_command(self, sys_cmd, dialog_context, service_registry, **kwargs):
        handler = self.msg_dispatch_tbl.get(str(sys_cmd.cmdspec))
        if not handler:
            return 'No handler registered in SMS DialogEngine for system command %s.' % sys_cmd.cmdspec.command
        return handler(sys_cmd, dialog_context, service_registry)


    def reply_command(self, command_input, dialog_context, service_registry, **kwargs):
        # command types: generator, syscommand, prefix
        if command_input.cmd_type == 'prefix':
            return self._reply_prefix_command(command_input.cmd_object, dialog_context, service_registry)

        elif command_input.cmd_type == 'syscommand':
            return self._reply_sys_command(command_input.cmd_object, dialog_context, service_registry)

        elif command_input.cmd_type == 'generator':
            return self._reply_generator_command(command_input.cmd_object, dialog_context, service_registry)

        else:
            raise Exception('Unrecognized command input type %s.' % command_input.cmd_type)


class SMSResponder(object):
    def __init__(self, engine: DialogEngine, lexicon: CommandLexicon, sms_service: SMSService, prefix_separator='-'):
        self.dialog_engine = engine
        self.parser = SMSMessageParser(lexicon, prefix_separator)
        self.sms_service = sms_service


    def respond(self, source_number, raw_message_body, service_registry):
        mobile_number = normalize_mobile_number(source_number)
        
        user = self.lookup_user(source_number)
        dlg_context = SMSDialogContext(user=user, source_number=mobile_number, message=unquote_plus(raw_message_body))

        try:
            command_input = self.parser.parse_sms_message_body(raw_message_body)
            print('#----- Resolved command: %s' % str(command_input))

            response = self.dialog_engine.reply_command(command_input, dlg_context, service_registry)
            self.sms_service.send_sms(mobile_number, response)

        except IncompletePrefixCommand as err:
            print('Error data: %s' % err)
            print('#----- Incomplete prefix command: in message body: %s' % raw_message_body)
            self.sms_service.send_sms(mobile_number, SMS_PREFIX_COMMAND_SPECS[raw_message_body].definition)

            raise

        except UnrecognizedSMSCommand as err:
            print('Error data: %s' % err)
            print('#----- Unrecognized system command: in message body: %s' % raw_message_body)
            self.sms_service.send_sms(mobile_number, self.lexicon.compile_help_string())
            
            raise
        

def load_lexicon(yaml_config: dict) -> CommandLexicon:
    
    lexicon = CommandLexicon()

    sys_cmd_segment = yaml_config.get('system_commands')
    if not sys_cmd_segment:
        raise Exception('YAML configuration does not contain a required "system_commands" section.')

    for cmd_name, cmd_def in sys_cmd_segment.items():
        defstring = cmd_def['definition']
        arg_required = cmd_def['arg_required']
        synonyms = cmd_def.get('synonyms', [])

        command_spec = SMSCommandSpec(command=cmd_name, definition=defstring, synonyms=synonyms, tag_required=arg_required)
        lexicon.register_sys_command_spec(command_spec)

    gen_cmd_segment = yaml_config.get('generator_commands')
    if not gen_cmd_segment:
        raise Exception('YAML configuration does not contain a required "generator_commands" section.')

    for cmd_name, cmd_def in gen_cmd_segment.items():
        defstring = cmd_def['definition']
        specifier = cmd_def['specifier']
        filter_char = cmd_def['filter_char']

        command_spec = SMSGeneratorSpec(command=cmd_name, definition=defstring, specifier=specifier, filterchar=filter_char)
        lexicon.register_gen_command_spec(command_spec)

    prefix_cmd_segment = yaml_config.get('prefix_commands')
    if not prefix_cmd_segment:
        raise Exception('YAML configuration does not contain a required "prefix_commands" section.')

    for cmd_name, cmd_def in prefix_cmd_segment.items():
        defstring = cmd_def['definition']
        separator = cmd_def['separator']

        command_spec = SMSPrefixSpec(command=cmd_name, definition=defstring, defchar=separator)
        lexicon.register_pfx_command_spec(command_spec)

    return lexicon


def load_dialog_engine(yaml_config: dict, service_registry):
    pass


def load_command_dispatcher(yaml_config: dict, service_registry):
    pass