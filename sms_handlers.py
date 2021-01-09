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

    # under the covers, this will mean subscribing to a Kafka topic
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


def coalesce(delimiter, *modifiers):
    tokens = []
    for m in modifiers:
        if m.startswith(delimiter):
            tokens.append(m.lstrip(delimiter))
        elif m.endswith(delimiter):
            tokens.append(m.rstrip(delimiter))
            break
        else:
            tokens.append(m)
    
    return ' '.join(tokens)


def pulse_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if not len(cmd_object.modifiers):
        return f'usage: {cmd_object.cmdspec.command} <message> <user>'        
    
    message = coalesce('"', *cmd_object.modifiers[0: -1])

    # if the userid string is of the format "@<user>", then send message to the named user on THIS Pulse server.
    # If the userid string is of the format "@<server>.<user>", then send message to the named user on 
    # registered remote server <server>. (The server has to have been previously registered as a remote.)
    
    return f'message "{message}" sent to your outgoing stream.'


def send_private_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    if len(cmd_object.modifiers) < 2:
        return f'usage: {cmd_object.cmdspec.command} <message> <user>'
    
    message = coalesce('"', *cmd_object.modifiers[0:-1])
    userid = cmd_object.modifiers[-1]

    # if the userid string is of the format "<user>", then send message to the named user on THIS Pulse server.
    # If the userid string is of the format "<server>.<user>", then send message to the named user on 
    # registered remote server <server>. (The server has to have been previously registered as a remote.)

    return f'private message "{message}" sent to user {userid}.'
    

def forward_private_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    if len(cmd_object.modifiers) < 2:
        return f'usage: {cmd_object.cmdspec.command} <message_ID> <user>'
    
    # TODO: change this. We can only forward messages by ID
    message = coalesce('"', *cmd_object.modifiers[0:-1])
    userid = cmd_object.modifiers[-1]

    # if the userid string is of the format "<user>", then send message to the named user on THIS Pulse server.
    # If the userid string is of the format "<server>.<user>", then send message to the named user on 
    # registered remote server <server>. (The server has to have been previously registered as a remote.)

    return f'private message "{message}" forwarded to user {userid}.'
    

def archive_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    return 'archiving'


def message_details(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'showing message details'


def register_remote_pulse_server(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'registered remote server.'


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




