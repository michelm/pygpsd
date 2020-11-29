#!/usr/bin/python3
# -*- encoding: utf-8 -*-
# Michel Mooij, michel.mooij@dynniq.com

'''
DESCRIPTION
===========
Simulated GPS daemon. 
Can be used to test GPS client applications based on provided nmea file.

USAGE
=====
Command line usage:
    pygpsd <options>

Where options is one of:
    -i  --ip=<hostname|ip>      IP address of hostname of the server 
                                (default: localhost)
    -p  --port=<number>         Bind port of the server (default: 2948)
    -f  --fname=<path-to-nmea>  File containing nmea messages for the server
    -v  --version               prints version
    -h  --help                  displays this help
'''

import os, sys, getopt, asyncio, logging, socket
import pynmea2
import pygpsd
from pygpsd.server import Server, GPSDaemon


def usage():
    print(__doc__)


def get_socket(host: str, port: int) -> socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(3)
    sock.bind((host,port))
    sock.listen(10)
    return sock


def init_logging(logfile: str or None, level=logging.INFO) -> None:
    logfmt = 'pygpsd %(asctime)s %(levelname)-8s %(message)s'
    datefmt='%y-%m-%d %H:%M:%S'

    if not logfile:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt)
        return

    logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, filename=logfile, filemode='w')
    formatter = logging.Formatter('pygpsd %(asctime)s %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    

def main(argv=sys.argv, level=logging.INFO):
    host = 'localhost'
    port = 2948
    fname = None
    logfile = None
    
    try:
        opts, _ = getopt.getopt(argv[1:], 'i:p:f:l:vh', ['ip=', 'port=', 'fname=', 'version', 'help'])

        for opt, arg in opts:
            if opt in ('-i', '--ip'):
                host = arg
            elif opt in ('-p', "--port"):
                port = int(arg)
            elif opt in ('-f', '--fname'):
                fname = arg
            elif opt in ('-v', '--version'):
                print(pygpsd.version)
                sys.exit()
            elif opt in ('-h', '--help'):
                usage()
                sys.exit()
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if not fname:
        fname = os.path.join(os.path.dirname(__file__), 'data', 'example.nmea')

    init_logging(logfile, level)

    messages = []
    with open(fname, 'r') as f:
        lines = f.read().splitlines()
    for line in lines:
        msg = pynmea2.parse(line, check=False)
        messages.append(msg)

    device = '/dev/pts/1'
    version = { 'version':'3.20', 'rev':'3.20', 'proto_major':3, 'proto_minor':1 }
    daemon = GPSDaemon(version, device)

    sock = get_socket(host, port)
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: Server(loop, daemon, messages), sock=sock)
    server = loop.run_until_complete(coro)

    logging.info(f'serving on : {server.sockets[0].getsockname()}')
    logging.info(f'nmea file  : {fname}')
    logging.info(f'logfile    : {logfile}')

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info('keyboard interrupt, canceling tasks...')
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
    
    logging.info('bye')


if __name__ == '__main__':
    main(argv=sys.argv, level=logging.INFO)

