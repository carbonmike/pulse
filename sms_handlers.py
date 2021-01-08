#!/usr/bin/env python

import os, sys
from snap import common
from smslang import SMSDialogContext, CommandLexicon
from smslang import SystemCommand, GeneratorCommand, FunctionCommand



def handle_user_online(cmd_object: SystemCommand, dlg_context: SMSDialogContext, lexicon: CommandLexicon, service_registry, **kwargs) -> str:
    #return '\n\n placeholder for user-online handler'
    #print(cmd_object.modifiers)
    return 'User online.'


def handle_user_offline(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'User offline.'
    

def connect_user_stream(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if not len(cmd_object.modifiers):
        return f'The "{cmd_object.cmdspec.command}" command requires a @user parameter.'

    return f'connected stream from user {cmd_object.modifiers[0]}'


def disconnect_user_stream(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if not len(cmd_object.modifiers):
        return f'The "{cmd_object.cmdspec.command}" command requires a @user parameter.'

    return f'disconnected stream from user {cmd_object.modifiers[0]}'


def mute_messages(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if len(cmd_object.modifiers):
        userid = cmd_object.modifiers[0]
        return f'stream from user {userid} muted.'
    return 'all streams muted.'


def unmute_messages(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if len(cmd_object.modifiers):
        userid = cmd_object.modifiers[0]
        return f'stream from user {userid} unmuted.'
    return 'all streams unmuted.'


def forward_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    return 'forwarding message'


def archive_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    return 'archiving'


def message_details(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'showing message details'


def display_help_prompts(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if len(cmd_object.modifiers):
        # calling "help" and passing a command string gives the help string for that command only
        help_target = cmd_object.modifiers[0]        
        cmdspec = lexicon.match_sys_command(help_target)
        if not cmdspec:
            return f'no such command "{help_target}".'
        return f'command "{help_target}": {cmdspec.definition}'
    
    # calling "help" by itself gives you the help strings for all commands
    return lexicon.compile_help_string()




