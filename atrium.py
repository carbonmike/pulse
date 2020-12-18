#!/usr/bin/env python


'''

'''

import os, sys
import json
from abc import ABC


class MessagingContext(object):
    def __init__(self):
        pass

class MessageWriter(ABC):
    def __init__(self):
        pass

    
    def write_message(self, stream_id, **kwargs):
        pass


class MessageCollector(ABC):
    def __init__(self):
        pass

    def collect_messages(self, stream_id):
        pass


class MessageStream(object):
    def __init_(self):
        pass


class Exchange(object):
    def __init__(self, message_writer, message_collector, **kwargs):
        pass

