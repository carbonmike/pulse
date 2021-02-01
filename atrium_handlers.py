#!/usr/bin/env python

from atriumd import MessageHandler

class UnknownMessageHandler(MessageHandler):
    def __init__(self, channel_id:str, backchannel_id:str, timeout_seconds:int, **kwargs):
        super().__init__(channel_id, backchannel_id, timeout_seconds, **kwargs)


    def handle_message(self, message, backchannel_id):
        #return super().handle_message(message, backchannel_id)
        print(f'### Dummy handler invoked for unknown-type message: {message}')


class TestMessageHandler(MessageHandler):
    def __init__(self, channel_id:str, backchannel_id:str, timeout_seconds:int, **kwargs):
        super().__init__(channel_id, backchannel_id, timeout_seconds, **kwargs)


    def handle_message(self, message, backchannel_id):
        #return super().handle_message(message, backchannel_id)
        print(f'### Dummy handler invoked for test-type message: {message}')