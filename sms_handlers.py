#!/usr/bin/env python

import os, sys

from smslang import SMSDialogContext
from smslang import SystemCommand, GeneratorCommand, FunctionCommand


def handle_user_online(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    #return '\n\n placeholder for user-online handler'
    return 'Yup, you are online now.'


def handle_user_offline(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return '\n\n placeholder for user-offline handler'
    

def connect_user_stream(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'connected'


def disconnect_user_stream(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'disconnected'


def mute_messages(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'messages muted'


def unmute_messages(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'messages unmuted'


def forward_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'forwarding message'


def archive_message(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'archiving'


def message_details(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:
    return 'showing message details'


def display_help_prompts(cmd_object, dlg_context, lexicon, service_registry, **kwargs) -> str:    
    return lexicon.compile_help_string()




