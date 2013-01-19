#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from twisted.internet import reactor, protocol


# a client protocol

class InClient(protocol.Protocol):
    # {username: connection_id}
    users = {}
    # {connection_id: nethud.proto.client}
    clients = {}
    def dataReceived(self, data):
        print "Server said:", data
        # send all the things to the applicable clients
        jdata = json.loads(data)
        if 'auth' in jdata.keys():
            print jdata['auth']['connection']
            users[jdata['auth']['username']] = jdata['auth']['connection']
        self.send_message(data)

    def connectionLost(self, reason):
        print "Connection lost"

    def send_message(self, command, **kw):
        data = json.dumps({command: kw})
        print "Client says:", data
        self.transport.write(data.encode('utf8'))


class InFactory(protocol.ClientFactory):
    protocol = InClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()
