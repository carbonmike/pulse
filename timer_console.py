#!/usr/bin/env python

import time
from contextlib import ContextDecorator


class start_timer(ContextDecorator):
    def __init__(self):
        super().__init__()
        self.start_time = None 

    def __enter__(self):
        self.start_time = time.time()
        return self

    def poll_seconds(self):
        return int(time.time() - self.start_time)

    def __exit__(self, *exc):
        return False


def main():

    with start_timer() as t:
        time.sleep(2)
        print('Elapsed time: %s' % t.poll_seconds())
        time.sleep(1)
        print('New elapsed time: %s' % t.poll_seconds())



    print('done.')

if __name__ == '__main__':
    main()

