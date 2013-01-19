#
from nethud.proto import tee
from nethud.proto import client
from twisted.internet import reactor
from twisted.internet.protocol import Factory


def run_tee():
    factory = Factory()
    factory.protocol = tee.TeeFromClientProtocol
    reactor.listenTCP(12435, factory, interface="0.0.0.0")
    reactor.run()


def run_hudserv():
    factory = client.NethackFactory()
    reactor.listenTCP(55555, factory, interface="127.0.0.1")
    reactor.run()
