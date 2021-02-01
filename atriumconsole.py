#!/usr/bin/env python


'''
Usage:
    atriumconsole.py --config <configfile> --channel <channel_id> --message-data=<name:value>...
    atriumconsole.py --config <configfile> --channel <channel_id> -s
'''

import os, sys
import json
from multiprocessing import Process
import docopt
import redis
import utils
from snap import common
from abc import ABC


def parse_cli_params(params_array):
    data = {}
    if len(params_array):
        params_string = params_array[0]
        nvpair_tokens = params_string.split(',')
        for nvpair in nvpair_tokens:
            if ':' not in nvpair:
                raise Exception('parameters passed to warp must be in the format <name:value>.')

            tokens = nvpair.split(':') 
            key = tokens[0]
            value = tokens[1]
            data[key] = value

    return data



def main(args):
    print(common.jsonpretty(args))

    channel_id = 'atriumd_ipc_rcv_channel'
    msg_params = args['--message-data']

    
    #print(msg_dict)
    
    redis_params = {
        'host': '172.25.0.2',
        'port': 6379,
        'db': 0
    }


    redis_client = redis.StrictRedis(**redis_params)

    if args['-s']:
        raw_input = []
        for line in utils.read_stdin():
            raw_input.append(line)
        json_string = ''.join(raw_input)
        msg_dict = json.loads(json_string)

    else:
        msg_dict = parse_cli_params(msg_params)
    
    num_subscribers = redis_client.publish(channel_id, json.dumps(msg_dict))
    print(f'message sent to {num_subscribers} subscribers.')


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)