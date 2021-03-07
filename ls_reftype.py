#!/usr/bin/env python


'''
Usage:
    ls_reftype --config <configfile> --type <reftype>
    ls_reftype --config <configfile> --all
'''


import os, sys
import json
from snap import common
import docopt


def main(args):
    pass


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)



