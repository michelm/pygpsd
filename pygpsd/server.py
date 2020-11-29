#!/usr/bin/python3
# -*- encoding: utf-8 -*-
# Michel Mooij, michel.mooij@dynniq.com

import os, sys, re, asyncio, logging, json, typing
from typing import Dict
import pynmea2


class GPSDaemon:
    def __init__(self, version: Dict, device:str='/dev/pts/1'):
        self.ver = {
            'class':'VERSION',
            'version':version['version'],
            'rev':version['rev'],
            'proto_major':version['proto_major'],
            'proto_minor':version['proto_minor']
        }
        self.device = device
        self.mode = 0
        self.quality = 0
        self.status = 'V'
        self.timestamp = '135454.873'
        self.datestamp = '291120'
        self.lat = None
        self.lat_dir = 'N'
        self.lon = None
        self.lon_dir = 'E'
        self.speed = None
        self.heading = None
        self.altitude = None

    def parse(self, s: str) -> None:
        msg = pynmea2.parse(s, check=False)

        if isinstance(msg, pynmea2.types.talker.RMC):            
            self.timestamp = msg.data[0]
            self.status = msg.data[1]
            self.lat = msg.data[2]
            self.lat_dir = msg.data[3]
            self.lon = msg.data[4]
            self.lon_dir = msg.data[5]
            self.speed = float(msg.data[6]) # spd_over_grnd
            self.heading = float(msg.data[7]) # true_course
            self.datestamp = msg.data[8]

        elif isinstance(msg, pynmea2.types.talker.GGA):
            self.quality = int(msg.data[5])
            self.altitude = float(msg.data[8])

        elif isinstance(msg, pynmea2.types.talker.GSA):
            self.mode = int(msg.data[1])

    @property
    def version(self) -> str:
        return self.ver

    @property
    def date(self) -> str:
        d, m, y = re.findall('..',self.datestamp)
        s = f'{"20" if int(y) < 70 else "19"}{y}:{m}:{d}'
        return s

    @property
    def time(self) -> str:
        t, f = self.timestamp.split('.')
        h, m, s = re.findall('..',t)
        return f'{h}:{m}:{s}.{f}'

    @property
    def tpv(self) -> Dict:
        tpv = {
            'class':'TPV',
            'device': self.device,
            'time':f'{self.date}T{self.time}Z',
            'mode':self.mode
        }

        if self.mode >= 2:
            if self.lat != None and self.lon != None:
                tpv['lat'] = f'{"+" if self.lat_dir=="N" else "-"}{self.lat}'
                tpv['lon'] = f'{"+" if self.lat_dir=="E" else "-"}{self.lon}'
            if self.heading != None:
                tpv['track'] = self.heading
            if self.speed != None:
                tpv['speed'] = self.speed # in knots
        if self.mode == 3:
            if self.altitude != None:
                tpv['alt'] = self.altitude

        return tpv


class Server(asyncio.Protocol):
    clients = {}
    
    def __init__(self, loop, daemon, messages):
        super(Server, self).__init__()
        self.name = None
        self.transport = None
        self.loop = loop
        self.daemon = daemon
        self.messages = messages

    def connection_made(self, transport):
        """Called when a new client has connected
        
        :param transport: asyncio transport handle
        """
        self.name = transport.get_extra_info('peername')
        logging.info(f'session({self.name}) client connected')
        self.transport = transport
        Server.clients[self.name] = self

    def connection_lost(self, exc):
        """Called when a client connection is lost, for whatever reason
        
        :param exc: Exception object or None
        """
        logging.info(f'session({self.name}) client disconnected')
        if self.name in Server.clients.keys():
            del Server.clients[self.name]

    def send(self, data):
        """Send data to the client
        """
        if not self.transport:
            logging.warn(f'session({self.name}); send {len(data)} bytes, skipped; got no transport')
            return
        
        logging.info(f'session({self.name}); sending {len(data)} bytes')
        self.transport.write(data)

    def data_received(self, data):
        """Process a buffer of characters received from the client
        
        The received character will be added to the receive buffer. The combined
        result will be evaluated; when balanced and valid JSON the result will be
        processed on the session layer.
        
        :param data: received bytes
        """
        logging.info(f'session({self.name}); received {len(data)} bytes')
        
