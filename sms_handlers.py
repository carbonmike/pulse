#!/usr/bin/env python

import os, sys
from snap import common
from smslang import SMSDialogContext, CommandLexicon
from smslang import SystemCommand, GeneratorCommand, FunctionCommand


class UserNotFound(Exception):
    def __init__(self, username):
        super().__init__(self,  f'no such user ({username})')


def handle_user_online(cmd_object: SystemCommand, dlg_context: SMSDialogContext, lexicon: CommandLexicon, service_registry, **kwargs) -> str:
    #return '\n\n placeholder for user-online handler'
    #print(cmd_object.modifiers)

    if len(cmd_object.modifiers) < 2:
        return f'Usage: {cmd_object.cmdspec.command} <username>'
        
    atrium_svc = service_registry.lookup('atrium')

    username = cmd_object.modifiers[0]
    user_sms_number = dlg_context.source_number

    try:
        # sessions created in this way are not "secure" in that: 
        # (1) if your terminal (the mobile phone) is compromised, the session is compromised
        # (2) SMS is transmitted in the clear from your mobile to the nearest tower.
        #
        # We feel this is an acceptable compromise, because SMS is not the only usage mode
        # AND the SMS traffic in that mode does not disclose account information. 
        # Pulse will also offer endusers the ability to provision a mobile phone terminal 
        # for a limited amount of time, and to lock out that terminal on a moment's notice.
        # (The SMS interface does not expose the ability to perform any administrative actions
        # on the user's own account, limiting the damage an unauthorized user can do to your account 
        # if they get a hold of your phone.
        #
        # If you wish to send data to your Pulse stream and you want that data to be private,
        # you must interact with Pulse via the web interface.
        #
        session = atrium_svc.open_user_session_sms(user_sms_number, username, hold_until_verified=False)
    except Exception as err:
        return f'error creating user session: {str(err)}'

    return 'User online.'


def handle_user_offline(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    atrium_svc = service_registry.lookup('atrium')
    
    user_sms_number = dlg_context.source_number
    session = atrium_svc.get_user_session_sms(user_sms_number) # may return more than one?
    atrium_svc.close_session(session)

    return 'User offline.'


def connect_user_stream(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if not len(cmd_object.modifiers):
        return f'The "{cmd_object.cmdspec.command}" command requires a <user> parameter.'

    target_user = cmd_object.modifiers[0]
    atrium_svc = service_registry.lookup('atrium')
    user_sms_number = dlg_context.source_number

    session = atrium_svc.get_user_session_sms(user_sms_number)
    try:
        atrium_svc.connect_user_stream(target_user, session)

        # under the covers, this will mean subscribing to a Kafka topic
        return f'connected to pulse stream from user {cmd_object.modifiers[0]}'
    except UserNotFound as err:
        return f'error connecting to user stream: {str(err)}'


def disconnect_user_stream(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    if not len(cmd_object.modifiers):
        return f'The "{cmd_object.cmdspec.command}" command requires a @user parameter.'

    target_user = cmd_object.modifiers[0]
    atrium_svc = service_registry.lookup('atrium')
    user_sms_number = dlg_context.source_number

    session = atrium_svc.get_user_session_sms(user_sms_number)
    try:
        atrium_svc.disconnect_user_stream(target_user, session)
        return f'disconnected stream from user {cmd_object.modifiers[0]}'
    except UserNotFound as err:
        return f'error disconnecting from user stream: {str(err)}'


def mute_messages(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    atrium_svc = service_registry.lookup('atrium')
    user_sms_number = dlg_context.source_number        
    session = atrium_svc.get_user_session_sms(user_sms_number)

    if len(cmd_object.modifiers):
        target_user_id = cmd_object.modifiers[0]

        try:
            atrium_svc.mute_stream(target_user_id, session)        
            return f'stream from user {target_user_id} muted.'

        except UserNotFound as err:
            return f'error muting user stream: {str(err)}'

    atrium_svc.mute_all_streams(session)
    return 'all streams muted.'


def unmute_messages(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    atrium_svc = service_registry.lookup('atrium')
    user_sms_number = dlg_context.source_number        
    session = atrium_svc.get_user_session_sms(user_sms_number)

    if len(cmd_object.modifiers):
        target_user_id = cmd_object.modifiers[0]

        try:
            atrium_svc.unmute_stream(target_user_id, session)
            return f'stream from user {userid} unmuted.'
        except UserNotFound as err:
            return f'error muting user stream: {str(err)}'

    atrium_svc.unmute_all_streams(session)
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


def send_pulse(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    if not len(cmd_object.modifiers):
        return f'usage: {cmd_object.cmdspec.command} <message> <user>'        
    
    
    atrium_svc = service_registry.lookup('atrium')
    user_sms_number = dlg_context.source_number        
    session = atrium_svc.get_user_session_sms(user_sms_number)

    try:
        message = coalesce('"', *cmd_object.modifiers[0: -1])
        atrium_svc.pulse(message, session)
        return f'pulse sent.'
    
    except MessageFormatError as err:
        return f'a message containing spaces must begin and end with quotes.'

    except PulseNetworkError as err:
        return f'network error while attempting to send pulse.'


def send_private_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    if len(cmd_object.modifiers) < 2:
        return f'usage: {cmd_object.cmdspec.command} <message> <user>'
    
    atrium_svc = service_registry.lookup('atrium')
    user_sms_number = dlg_context.source_number
    session = atrium_svc.get_user_session_sms(user_sms_number)
    
    try:
        # if the userid string is of the format "<user>", then send message to the named user on THIS Pulse server.
        # If the userid string is of the format "<server>.<user>", then send message to the named user on 
        # registered remote server <server>. (The server has to have been previously registered as a remote.)

        message = coalesce('"', *cmd_object.modifiers[0:-1])
        target_user_id = cmd_object.modifiers[-1]    
        atrium_svc.send(message, target_user_id, session)

        return f'private message "{message}" sent to user {target_user_id}.'
    
    except MessageFormatError as err:
        return f'error: {err}'

    except PulseNetworkError as err:
        return f'network error while attempting to send private message.'
    

def forward_private_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:

    if len(cmd_object.modifiers) < 2:
        return f'usage: {cmd_object.cmdspec.command} <message_id> <user>'
        
    atrium_svc = service_registry.lookup('atrium')
    user_sms_number = dlg_context.source_number
    session = atrium_svc.get_user_session_sms(user_sms_number)

    message_id = cmd_object.modifiers[0]
    target_user_id = cmd_object.modifiers[1]

    try:
        # if the userid string is of the format "<user>", then send message to the named user on THIS Pulse server.
        # If the userid string is of the format "<server>.<user>", then send message to the named user on 
        # registered remote server <server>. (The server has to have been previously registered as a remote.)

        atrium_svc.forward_message(message_id, target_user_id, session)
        return f'private message [{message_id}] forwarded to user {target_user_id}.'

    except:
        return f'error forwarding private message to user {target_user_id}.'
    

def archive_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'placeholder for archiving function'


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




