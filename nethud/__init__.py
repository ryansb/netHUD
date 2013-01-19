#
from nethud.proto import tee
from twisted.internet import reactor
from twisted.internet.protocol import Factory


def run_tee():
    factory = Factory()
    factory.protocol = tee.TeeFromClientProtocol
    reactor.listenTCP(12435, factory, interface="0.0.0.0")
    reactor.run()


