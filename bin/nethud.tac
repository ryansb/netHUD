#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.application import service
from twisted.application.internet import TCPServer
from twisted.internet.protocol import Factory

from nethud.proto.tee import TeeFromClientProtocol
from nethud.proto.telnet import TelnetFactory


class TeeService(service.Service):
    """On a silver platter"""
    def getFactory(self):
        f = Factory()
        f.protocol = TeeFromClientProtocol
        return f


class TelnetService(service.Service):
    def get_factory(self):
        return TelnetFactory()


application = service.Application('nethud')

s = TeeService()

serviceCollection = service.IServiceCollection(application)
TCPServer(53421, s.getFactory(), interface="0.0.0.0"
          ).setServiceParent(serviceCollection)

TCPServer(53421, s.getFactory(), interface="::1"
          ).setServiceParent(serviceCollection)

tns = TelnetService()
TCPServer(2323, tns.get_factory(), interface='0.0.0.0') \
    .setServiceParent(serviceCollection)
