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

from pulse_services import SMSService

from snap import common

SMSCommandSpec = namedtuple('SMSCommandSpec', 'command definition synonyms tag_required')
SMSGeneratorSpec = namedtuple('SMSGeneratorSpec', 'command definition specifier filterchar')
SMSFunctionSpec = namedtuple('SMSFunctionSpec', 'command definition defchar')

SystemCommand = namedtuple('SystemCommand', 'content_tag cmdspec modifiers')
GeneratorCommand = namedtuple('GeneratorCommand', 'cmd_string cmdspec modifiers')
FunctionCommand = namedtuple('FunctionCommand', 'mode tag function_name body cmdspec') # modes: define, call

CommandInput = namedtuple('CommandInput', 'cmd_type cmd_object')  # command types: generator, syscommand, function

SMSDialogContext = namedtuple('SMSDialogContext', 'user source_number message')


class UnrecognizedSMSCommand(Exception):
    def __init__(self, cmd_string):
        super().__init__(self, 'Invalid SMS command %s' % cmd_string)


class IncompleteFunctionCommand(Exception):
    def __init__(self, cmd_string):
        super().__init__(self, 'Incomplete function command %s' % cmd_string)


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


class MacroCommand(object):
    def __init__(self, name, *command_line):
        self.name = name
        self.body = ' '.join(command_line)

    def evaluate(self):
        return self.body


class CommandLexicon(object):
    def __init__(self):
        self.system_commands = {}
        self.generator_commands = {}
        self.function_commands = {}
        self.command_macros = {}

    def system_spec(self, cmd: SystemCommand):
        return self.system_commands[cmd]


    def register_sys_command_spec(self, cmdspec: SMSCommandSpec):
        self.system_commands[cmdspec.command] = cmdspec
        

    def register_gen_command_spec(self, cmdspec: SMSGeneratorSpec):
        self.generator_commands[cmdspec.command] = cmdspec


    def register_func_command_spec(self, cmdspec: SMSFunctionSpec):
        self.function_commands[cmdspec.command] = cmdspec


    def register_command_macro_spec(self):
        pass

    def supports_function_command(self, tag):
        return tag in self.function_commands


    def match_sys_command(self, cmd_string):
        for key, cmd_spec in self.system_commands.items():
            if cmd_string == key:
                return cmd_spec
            if cmd_string in cmd_spec.synonyms:
                return cmd_spec

        return None

    def match_generator_command(self, cmd_string):
        for key, cmd_spec in self.generator_commands.items():
            delimiter = cmd_spec.specifier
            filter_char = cmd_spec.filterchar

            #print('the filter character is [%s].' % filter_char)

            if cmd_string.split(delimiter)[0] == key:
                return cmd_spec

            if cmd_string.split(filter_char)[0] == key:
                return cmd_spec

        return None


    def match_function_command(self, cmd_string):
        for key, cmd_spec in self.function_commands.items():            
            if cmd_string[0] == key:
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

        lines.append('[ FUNCTION commands ]:')
        for key, cmd_spec in self.function_commands.items():
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
        content_tag = None
        command_string = None
        modifiers = []

        # make sure there's no leading whitespace, then see what we've got
        body = unquote_plus(raw_body).lstrip().rstrip().lower()

        '''
        print('\n\n###__________ inside parse logic. Raw message body is:')
        print(body)
        print('###__________\n\n')
        '''

        body_prefix = body.split(self.prefix_separator)[0]
        prefix_handler = self.systemdata_prefix_handlers.get(body_prefix)
        if prefix_handler:

            # remove the URL encoded whitespace chars;
            # remove any trailing/leading space chars as well
            tokens = [token.lstrip().rstrip() for token in body.split(' ') if token]

            #print('###------ message tokens: %s' % common.jsonpretty(tokens))

            content_tag = tokens[0]
            if len(tokens) == 2:
                command_string = tokens[1].lower()

            if len(tokens) > 2:
                command_string = tokens[1].lower()
                modifiers = tokens[2:]

            #print('#--------- looking up system SMS command: %s...' % command_string)
            command_spec = self.lexicon.lookup_sms_command(command_string)
            if command_spec:
                return CommandInput(cmd_type='syscommand', cmd_object=SystemCommand(content_tag=content_tag,
                                                                                    cmdspec=command_spec,
                                                                                    modifiers=modifiers))
            raise UnrecognizedSMSCommand(command_string)

        elif self.lexicon.supports_function_command(body[0]):

            command_name = body[0]
            command_spec = self.lexicon.match_function_command(body[0])
            tokens = body.split(command_spec.defchar)

            #print('### probable prefix command "%s". Body length is %d.' % (prefix, len(body)))

            if len(tokens) == 1:
                raise IncompleteFunctionCommand(command_string)

            
            raw_body = body[1:].lower()
            defchar_index = raw_body.find(command_spec.defchar)

            # when a prefix command is issued containing a defchar, that is its "define" mode
            if defchar_index > 0:            
                command_mode = 'define'
                function_name = raw_body[0:defchar_index]
                command_data = raw_body[defchar_index+1:]

            # prefix commands issued without the defchar are running in "call" mode
            else:
                command_mode = 'call'
                function_name = raw_body
                command_data = None

            return CommandInput(cmd_type='function',
                                cmd_object=FunctionCommand(mode=command_mode,                                                        
                                                           tag=command_name,
                                                           body=command_data,
                                                           function_name=function_name,
                                                           cmdspec=command_spec))

        else:
            tokens = [token.lstrip().rstrip() for token in body.split(' ') if token]
            command_string = tokens[0].lower()
            modifiers = tokens[1:]

            # see if we received a generator 
            # (a command which generates a list or a slice of a list)

            #print('******************* LOOKING UP GENERATOR CMD for string [%s]...' % command_string)
            command_spec = self.lexicon.match_generator_command(command_string)
            if command_spec:
                #print('###------------ detected GENERATOR-type command: %s' % command_string)            
                return CommandInput(cmd_type='generator',
                                    cmd_object=GeneratorCommand(cmd_string=command_string,
                                                                cmdspec=command_spec,
                                                                modifiers=modifiers))

            # if we didn't find a generator, perhaps the user issued a regular sms comand                                             
            command_spec = self.lexicon.match_sys_command(command_string)
            if command_spec:
                #print('###------------ detected system command: %s' % command_string)
                return CommandInput(cmd_type='syscommand',
                                    cmd_object=SystemCommand(content_tag=content_tag,
                                                            cmdspec=command_spec,
                                                            modifiers=modifiers))
        
            raise UnrecognizedSMSCommand(command_string)


class DialogEngine(object):
    def __init__(self):
        self.msg_dispatch_tbl = {}
        self.generator_dispatch_tbl = {}
        self.function_dispatch_tbl = {}


    def register_cmd_handler(self, sms_command_spec, handler_func):
        self.msg_dispatch_tbl[str(sms_command_spec)] = handler_func

    def register_generator_handler(self, generator_cmd_spec, handler_func):
        self.generator_dispatch_tbl[str(generator_cmd_spec)] = handler_func

    def register_function_handler(self, prefix_spec, handler_func):
        self.function_dispatch_tbl[str(prefix_spec)] = handler_func


    def _reply_function_command(self, function_cmd, dialog_context, lexicon, service_registry, **kwargs):
        command = self.function_dispatch_tbl.get(str(function_cmd.cmdspec))
        if not command:
            return 'No handler registered in SMS DialogEngine for function command %s.' % function_cmd.cmdspec.command
        return command(function_cmd, self, dialog_context, lexicon, service_registry)


    def _reply_generator_command(self, gen_cmd, dialog_context, lexicon, service_registry, **kwargs):
        list_generator = self.generator_dispatch_tbl.get(str(gen_cmd.cmdspec))
        if not list_generator:
            return 'No handler registered in SMS DialogEngine for generator command %s.' % gen_cmd.cmdspec.command
        return list_generator(gen_cmd, self, dialog_context, lexicon, service_registry)


    def _reply_sys_command(self, sys_cmd, dialog_context, lexicon, service_registry, **kwargs):
        handler = self.msg_dispatch_tbl.get(str(sys_cmd.cmdspec))
        if not handler:
            return 'No handler registered in SMS DialogEngine for system command %s.' % sys_cmd.cmdspec.command
        return handler(sys_cmd, dialog_context, lexicon, service_registry)


    def reply_command(self, command_input, dialog_context, lexicon, service_registry, **kwargs):
        # command types: generator, syscommand, prefix
        if command_input.cmd_type == 'function':
            return self._reply_prefix_command(command_input.cmd_object, dialog_context, lexicon, service_registry)

        elif command_input.cmd_type == 'syscommand':
            return self._reply_sys_command(command_input.cmd_object, dialog_context, lexicon, service_registry)

        elif command_input.cmd_type == 'generator':
            return self._reply_generator_command(command_input.cmd_object, dialog_context, lexicon, service_registry)

        else:
            raise Exception('Unrecognized command input type %s.' % command_input.cmd_type)


class SMSResponder(object):
    def __init__(self, engine: DialogEngine, lexicon: CommandLexicon, sms_service: SMSService, prefix_separator='-'):
        self.dialog_engine = engine
        self.lexicon = lexicon
        self.parser = SMSMessageParser(lexicon, prefix_separator)
        self.sms_service = sms_service


    def respond(self, source_number, raw_message_body, service_registry):
        mobile_number = normalize_mobile_number(source_number)
        
        user = self.lookup_user(source_number)
        dlg_context = SMSDialogContext(user=user, source_number=mobile_number, message=unquote_plus(raw_message_body))

        try:
            command_input = self.parser.parse_sms_message_body(raw_message_body)
            print('#----- Resolved command: %s' % str(command_input))

            response = self.dialog_engine.reply_command(command_input, dlg_context, self.lexicon, service_registry)
            self.sms_service.send_sms(mobile_number, response) 

        except IncompleteFunctionCommand as err:
            print('Error data: %s' % err)
            print('#----- Incomplete prefix command: in message body: %s' % raw_message_body)
            self.sms_service.send_sms(mobile_number, self.lexicon.lookup_function_command(raw_message_body[0]).definition)

            raise

        except UnrecognizedSMSCommand as err:
            print('Error data: %s' % err)
            print('#----- Unrecognized system command: in message body: %s' % raw_message_body)
            self.sms_service.send_sms(mobile_number, self.lexicon.compile_help_string())
            
            raise
        

def load_lexicon(yaml_config: dict) -> CommandLexicon:
    
    lexicon = CommandLexicon()

    sys_cmd_segment = yaml_config['command_sets'].get('system')
    if not sys_cmd_segment:
        raise Exception('YAML configuration does not contain a required [command_sets][system] section.')

    for cmd_name, cmd_def in sys_cmd_segment['commands'].items():
        defstring = cmd_def['definition']
        arg_required = cmd_def['arg_required']
        synonyms = cmd_def.get('synonyms', [])

        command_spec = SMSCommandSpec(command=cmd_name, definition=defstring, synonyms=synonyms, tag_required=arg_required)
        lexicon.register_sys_command_spec(command_spec)

    gen_cmd_segment = yaml_config['command_sets'].get('generator')
    if not gen_cmd_segment:
        raise Exception('YAML configuration does not contain a required "generator_commands" section.')

    specifier = gen_cmd_segment['settings']['specifier']
    filter_char = gen_cmd_segment['settings']['filter_char']
    for cmd_name, cmd_def in gen_cmd_segment['commands'].items():
        defstring = cmd_def['definition']        
        command_spec = SMSGeneratorSpec(command=cmd_name, definition=defstring, specifier=specifier, filterchar=filter_char)
        lexicon.register_gen_command_spec(command_spec)

    function_cmd_segment = yaml_config['command_sets'].get('function')
    if not function_cmd_segment:
        raise Exception('YAML configuration does not contain a required "function_commands" section.')

    defchar = function_cmd_segment['settings']['def_char']
    modchar = function_cmd_segment['settings']['mod_char']
    for cmd_name, cmd_def in function_cmd_segment['commands'].items():
        defstring = cmd_def['definition']
        modifiers = cmd_def.get('modifiers', [])
        command_spec = SMSFunctionSpec(command=cmd_name, definition=defstring, defchar=defchar)        
        lexicon.register_func_command_spec(command_spec)

    return lexicon


def load_dialog_engine(yaml_config: dict, lexicon: CommandLexicon, service_registry):
    engine = DialogEngine()
    handler_module_name = yaml_config['globals']['command_handler_module']

    # register handlers for system commands
    sys_handler_segment = yaml_config['command_sets']['system'].get('handlers') or {}
    for cmd_name, funcname in sys_handler_segment.items():
    
        cmd_spec = lexicon.match_sys_command(cmd_name)
        if not cmd_spec:
            raise Exception(f'No system command "{cmd_name}" has been registered; cannot assign handler function.')
        
        handler_function = common.load_class(funcname, handler_module_name)
        engine.register_cmd_handler(cmd_spec, handler_function)
    
    # register handler for generator commands
    gen_handler_segment = yaml_config['command_sets']['generator'].get('handlers') or {}
    for cmd_name, funcname in gen_handler_segment.items(): 
    
        cmd_spec = lexicon.match_generator_command(cmd_name)
        if not cmd_spec:
            raise Exception(f'No generator command "{cmd_name}" has been registered; cannot assign handler function.')

        handler_function = common.load_class(funcname, handler_module_name)
        engine.register_cmd_handler(cmd_spec, handler_function)
    
    # register function handlers for function-type commands
    func_handler_segment = yaml_config['command_sets']['function'].get('handlers') or {}
    for cmd_name, func_name in func_handler_segment.items():

        cmd_spec = lexicon.match_function_command(cmd_name)
        if not cmd_spec:
            raise Exception(f'No function command "{cmd_name}" has been registered; cannot assign handler function.')

        handler_function = common.load_class(funcname, handler_module_name)
        engine.register_cmd_handler(cmd_spec, handler_function)

    return engine


def load_command_dispatcher(yaml_config: dict, service_registry):
    pass