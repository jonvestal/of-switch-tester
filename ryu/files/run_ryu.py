#!/usr/bin/env python3

import sys

from ryu.cmd import manager


def main():
    sys.argv.append('--ofp-tcp-listen-port')
    sys.argv.append('6653')
    sys.argv.append('RyuToOpentsdb')
    sys.argv.append('TpnRyuUtils')
    sys.argv.append('ryu.app.ofctl_rest')
    sys.argv.append('--verbose')
    sys.argv.append('--enable-debugger')
    manager.main()

if __name__ == '__main__':
    main()