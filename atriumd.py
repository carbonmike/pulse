#!/usr/bin/env python


'''
Usage:
    atriumd.py --config <configfile>
'''

import os, sys
import json
from multiprocessing import Process
import docopt
import redis
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


def console_handler(message, service_registry):
    print(f'### console handler function received message: {message}')


class Dispatcher(object):
    def __init__(self, **kwargs):
        pass

    def get_handler_for_message_type(self, message):
        return console_handler


def main(args):
    print(args)

    redis_params = {
        'host': '172.25.0.2',
        'port': 6379,
        'db': 0
    }

    rcv_channel_id = 'atriumd_ipc_rcv_channel'
    send_channel_id = 'atriumd_ipc_send_channel'

    r = redis.StrictRedis(**redis_params)

    redis_pubsub_interface = r.pubsub()
    redis_pubsub_interface.subscribe(rcv_channel_id)

    dispatcher = Dispatcher()
    service_tbl = {}
    child_procs = []

    while True:
        print(f'> atriumd waiting for messages on channel "{rcv_channel_id}"...')
        print(f'{len(child_procs)} handler processes in pool.')
        message = redis_pubsub_interface.get_message(timeout=60)
        if message:

            print('> Message received. Invoking dispatch...')
            try:

                msg_handler_func = dispatcher.get_handler_for_message_type(message)
                if not msg_handler_func:
                    print(f'> No handler registered with atriumd for message type. Ignoring.')
                    continue

                p = Process(target=msg_handler_func, args=(message, service_tbl))
                p.start()
                child_procs.append(p)

                print('> Queued message-handling subprocess.')
                
            except Exception as err:
                    print('!!! Error processing inbound message: %s' % message)
                    print(err)

    

if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)