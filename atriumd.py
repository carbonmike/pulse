#!/usr/bin/env python


'''
Usage:
    atriumd.py --config <configfile>
'''

import os, sys
import json
import uuid
from collections import namedtuple
from multiprocessing import Process
import docopt
import redis
from abc import ABC
from uhashring import HashRing



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


class MessageHandler(ABC):
    def __init__(self, channel_id:str, backchannel_id:str, timeout_seconds:int, redis_params:dict):
        r = redis.StrictRedis(**redis_params)
        self.redis_pubsub_interface = r.pubsub()
        self.redis_pubsub_interface.subscribe(channel_id)
        self.backchannel_id = backchannel_id
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def handle_message(self, message:str, backchannel_id:str):
        pass

    def process(self):
        while True:
            message = self.redis_pubsub_interface.get_message(timeout=self.timeout_seconds)
            if message:
                self.handle_message(message, self.backchannel_id)



HandlerNode = namedtuple('HandlerNode', 'process_id target_channel atrium_channel')


class Switch(object):
    def __init__(self, **kwargs):        
        self.target_map = {}
        self.dispatch_table = {}        
        self.redis_params = kwargs['redis_params']


    def register_message_type(self, msg_type: str, handler_class: MessageHandler):
        self.target_map[msg_type] = handler_class


    def create_dispatch_target(self, message_type: str, handler_pool_size: int, rcv_channel: str, send_channel: str):
        '''A dispatch target consists of 1 to N handler nodes in a consistent hash ring
        '''

        handler_class = self.target_map.get(message_type)

        if not handler_class:
            raise Exception(f'No handler registered for message type {message_type}.')

        
        ring_nodes = {}
        for i in range(handler_pool_size):

            nodename = f'message_type_handler_node_{i}'

            # we create P handler instances where P is the poolsize; each handler is independent 
            # and does not share data with other instances
            handler = handler_class(rcv_channel, send_channel, 30, self.redis_params)

            # spawn the message handler as a process
            p = Process(target=handler.process)
            p.start()
            
            node = HandlerNode(process_id=p.pid,
                               receive_channel=rcv_channel,
                               send_channel=send_channel,
                               handler_class=handler_class,
                               handler_instance=handler)
            
            ring_nodes[nodename] = node
        
        # create the hash ring and add it to the dispatch table so that we can key on message type;
        # each inbound message (if it is of a recognized type) will be handled by one of the nodes
        # in the ring
        hash_ring = HashRing(ring_nodes)
        self.dispatch_table[message_type] = hash_ring


    def get_message_type(self, message):
        '''The Atrium IPC message format is:

            {
                message_type: <msg_type>,
                data_type: <mime_type>
                timestamp: <creation_timestamp>,
                sender_pid: <sender_process_id>,
                body: <message_data>
            }

        '''
        try:
            message_data = json.loads(message)

        
        except Exception as err:
            print(err)
            return 'unknown'
        


class SwitchBuilder(object):
    def __init__(self, atrium_channel_id):
        self._atrium_channel = atrium_channel_id

    def generate_channel_id(self, message_type: str)->str:
        return f'{message_type}_{uuid.uuid4()}'

    def build(self, yaml_config):

        switch = Switch()
        for msg_type, handler_config in yaml_config['message_types'].items():
            handler_pool_size = int(handler_config.get('pool_size', 1))
            rcv_channel_id = self.generate_channel_id(msg_type)
            switch.create_dispatch_target(msg_type, handler_pool_size, rcv_channel_id, self._atrium_channel)

        return switch


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