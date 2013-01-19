#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.application import service
from twisted.application.internet import TCPServer
from nethud.proto.tee import TeeFromClientProtocol
from twisted.internet.protocol import Factory


class TeeService(service.Service):
    """On a silver platter"""
    def getFactory(self):
        f = Factory()
        f.protocol = TeeFromClientProtocol
        return f


application = service.Application('nethud')

s = TeeService()

serviceCollection = service.IServiceCollection(application)
TCPServer(12435, s.getFactory(), interface="0.0.0.0"
          ).setServiceParent(serviceCollection)
