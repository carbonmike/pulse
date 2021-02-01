#!/usr/bin/env python


'''
Usage:
    atriumd.py --config <configfile>
'''

import os, sys
import json
import uuid
import datetime
import traceback
from collections import namedtuple
from multiprocessing import Process
import docopt
import redis
from abc import ABC, abstractmethod
from snap import common
from uhashring import HashRing



class BadMessageHeaderFormat(Exception):
    def __init__(self, field_name):
        super().__init__(self, f'Atrium message header is missing required field {field_name}.')


class UnregisteredMessageType(Exception):
    def __init__(self, msg_type):
        super().__init__(self, f'No message of type "{msg_type}" registered with Atrium server.')


def console_handler(message, service_registry):
    print(f'### console handler function received message: {message}')


class MessageHandler(ABC):
    def __init__(self, channel_id:str, backchannel_id:str, timeout_seconds:int, **kwargs):
        self.redis_client = redis.StrictRedis(**kwargs)
        self.redis_pubsub_interface = self.redis_client.pubsub()
        self.redis_pubsub_interface.subscribe(channel_id)
        self.backchannel_id = backchannel_id
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def handle_message(self, message:str, backchannel_id:str):
        pass


    def send_message(self, message_type, body_mimetype, **kwargs):
        '''Allows a message handler to communicate with its parent atriumd process
        by publishing to its pub/sub backchannel
        '''
         
        msg_dict = {
            'message_type': message_type,
            'body_data_type': body_mimetype,
            'timestamp': datetime.datetime.now().isoformat(),
            'sender_pid': -1,
            'body': json.dumps(kwargs)
        }

        self.redis_client.publish(self.backchannel_id, json.dumps(msg_dict))

    def process(self):
        while True:            
            message = self.redis_pubsub_interface.get_message(timeout=self.timeout_seconds)
            if message:
                if message['type'] == 'subscribe':
                    print('channel-subscription message detected at handler. Skipping.')
                else:
                    self.handle_message(message, self.backchannel_id)


HandlerNode = namedtuple('HandlerNode', 'process_id receive_channel send_channel handler_class handler_instance')

class Switch(object):
    def __init__(self, **kwargs):        
        self.target_map = {}
        self.dispatch_table = {}        
        self.redis_params = {
            'host': kwargs['redis_host'],
            'port': kwargs['redis_port'],
            'db': kwargs['redis_db']
        }

        self.redis_client = redis.StrictRedis(**self.redis_params)
        self.atrium_backchannel = kwargs['rcv_channel_id'] # for message handlers to communicate with atriumd


    def generate_channel_id(self, message_type: str)->str:
        return f'{message_type}_{uuid.uuid4()}'


    def register_message_type(self, msg_type: str, handler_class: MessageHandler):
        self.target_map[msg_type] = handler_class


    def add_dispatch_target(self, message_type: str, handler_pool_size: int):
        '''A dispatch target consists of 1 to N handler nodes in a consistent hash ring
        '''

        handler_class = self.target_map.get(message_type)

        if not handler_class:
            raise Exception(f'No handler registered for message type {message_type}.')

        
        ring_nodes = []
        for i in range(handler_pool_size):

            nodename = f'message_type_handler_node_{i}'
            rcv_channel = self.generate_channel_id(message_type)

            # we create P handler instances where P is the poolsize; each handler is independent 
            # and does not share data with other instances
            handler = handler_class(rcv_channel, self.atrium_backchannel, 30, **self.redis_params)

            # spawn the message handler as a process
            p = Process(target=handler.process)
            p.start()
            
            node = HandlerNode(process_id=p.pid,
                               receive_channel=rcv_channel,
                               send_channel=self.atrium_backchannel,
                               handler_class=handler_class,
                               handler_instance=handler)
            
            print(f'+++ adding handler node (PID {p.pid}) to dispatch target for message type "{message_type}":')
            print(f'+++ receive channel is {node.receive_channel}')
            
            ring_nodes.append(node)


        # create the hash ring and add it to the dispatch table so that we can key on message type;
        # each inbound message (if it is of a recognized type) will be handled by one of the nodes
        # in the ring
        hash_ring = HashRing(ring_nodes)

        #print(f'{len(hash_ring.nodes)} handler(s) in pool for message type {message_type}.')

        self.dispatch_table[message_type] = hash_ring


    def get_atrium_message_type(self, message):
        '''The Atrium IPC message format is:

            {
                message_type: <msg_type>,
                body_data_type: <mime_type>
                timestamp: <creation_timestamp>,
                sender_pid: <sender_process_id>,
                body: <message_data>
            }

        '''
        
        msg_string = message['data'].decode('UTF-8')
        msg_object = json.loads(msg_string)
        msg_type = msg_object.get('message_type')
            
        if not msg_type:
            raise BadMessageHeaderFormat(msg_string, 'message_type')
        
        return msg_type


    def forward(self, message:dict):
        try:            
            msg_type = self.get_atrium_message_type(message)
            print(f'+++ INBOUND message of type [{msg_type}] detected.')
            '''
            print('Message content:')
            print('______________________')
            print(message)
            print('______________________')
            '''

            hash_ring = self.dispatch_table.get(msg_type)
            if not hash_ring:
                raise UnregisteredMessageType(msg_type)

            timestamp_string = datetime.datetime.now().isoformat()
            handler_node = hash_ring.get_node(hash(timestamp_string))
            print('+++ Selected handler node:')
            print(handler_node)
            
            self.redis_client.publish(handler_node.receive_channel, message['data'])

        except BadMessageHeaderFormat as err:
            print('!!! inbound message either badly formatted (not JSON) or missing the message_type field.')
            raise


class SwitchBuilder(object):
    
    @staticmethod
    def build(yaml_config):

        switch = Switch(**yaml_config['settings'])
        handler_module_name = yaml_config['globals']['message_handler_module']

        for msg_type, handler_config in yaml_config['message_types'].items():
            
            handler_classname = handler_config['handler_class']
            handler_class = common.load_class(handler_classname, handler_module_name)
            switch.register_message_type(msg_type, handler_class)
            handler_pool_size = int(handler_config.get('handler_poolsize', 1))
            
            switch.add_dispatch_target(msg_type, handler_pool_size)

        return switch


def main(args):

    configfile_name = args['<configfile>']
    yaml_config = common.read_config_file(configfile_name)

    atrium_settings = yaml_config['settings']
    send_channel_id = atrium_settings['send_channel_id']
    rcv_channel_id = atrium_settings['rcv_channel_id']   

    switch = SwitchBuilder.build(yaml_config)

    redis_client = redis.StrictRedis(host=atrium_settings['redis_host'],
                                     port=atrium_settings['redis_port'],
                                     db=atrium_settings['redis_db'])

    redis_pubsub_interface = redis_client.pubsub()
    redis_pubsub_interface.subscribe(rcv_channel_id)


    while True:
        print(f'> atriumd waiting for messages on channel "{rcv_channel_id}"...')
        
        message = redis_pubsub_interface.get_message(timeout=60)
        if message:

            if message['type'] == 'subscribe':
                print(f'> subscribe-type message received in main atriumd event loop. Bypassing dispatch logic.')
                continue

            print('> Message received. Invoking dispatch...')
            try:
                switch.forward(message)
            except Exception as err:
                print('!!! Error processing inbound message: %s' % message)
                print(err)
                traceback.print_exc()


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)