from __future__ import unicode_literals
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientFactory, Factory
from nethud.controller import Controller
import json


"""
NOTE: This is heavily inspired by https://gist.github.com/1878983
"""
#Make sure to send auth to Nethud with both the client and sever json


class TeeFromClientProtocol(Protocol):
    """
    We are connected to by the client
    and forward messages from the client to the server and the hud
    """

    def connectionMade(self):
        """
        Called when the client connects to this object
        we use this to setup all our connections to other things,
        such as the hud, and the actual server
        """
        self.outgoing_queue = defer.DeferredQueue()
        self.outgoing_queue.get().addCallback(self.dataFromNetHack)
        self.incoming_queue = defer.DeferredQueue()
        self.hud_queue = defer.DeferredQueue()

        toNetHackFactory = TeeToNetHackFactory(self.incoming_queue,
                self.outgoing_queue, self.hud_queue)

        hudToController = TeeToHUDController(self.hud_queue)

        reactor.connectTCP("games-ng.csh.rit.edu", 53421, toNetHackFactory)

    def dataFromNetHack(self, data):
        """Data returned from the nethack server"""
        self.transport.write(data)
        self.outgoing_queue.get().addCallback(self.dataFromNetHack)

    def dataReceived(self, data):
        """
        Data from the nethack client
        We should only need to send the auth data to the hud all other client data may be irrelevent
        """
        self.incoming_queue.put(data)
        if "auth" in data:
            self.hud_queue.put(data)


class TeeToNetHackProtocol(Protocol):
    """
    We connect to the nethack server
    and return any messages received to both the client and the hud
    """

    def connectionMade(self):
        """
        Called when we connect to the nethack server
        """
        self.outgoing_queue = self.factory.outgoing_queue
        self.incoming_queue = self.factory.incoming_queue
        self.hud_queue = self.factory.hud_queue
        self.incoming_queue.get().addCallback(self.dataFromNetHackClient)
        self.authPacket = None

    def dataFromNetHackClient(self, data):
        """
        Used as a callback to grab data from the incoming queue and write it to
        the server
        """
        self.transport.write(data)
        self.incoming_queue.get().addCallback(self.dataFromNetHackClient)

    def dataReceived(self, data):
        """
        Take data coming from the server and put it into the queue for the
        client
        We are also doing a bit of checking to combine auth messages.
        """
        self.outgoing_queue.put(data)
        if "auth" in data and not self.authPacket:
            self.authPacket = json.loads(data)
        elif "auth" in data and self.authPacket:
            self.authPacket.update(json.loads(data)['auth'])
            self.hud_queue.put(json.dumps(self.authPacket))


class TeeToHUDController(object):
    """
    This class is hooked in to a deferred queue which gets messages from the client and server
    and uses controller.send_msg to push them out
    """
    def __init__(self, hud_queue):
        self.hud_queue = hud_queue
        self.hud_queue.get().addCallback(self.dataFromTeeReceived)
        self.user = ""

    def dataFromTeeReceived(self, data):
        jData = json.loads(data)
        if "auth" in data:
            if 'username' in jData['auth']
                self.user = jData['auth']['usename']

        if self.user != "":
            Controller.send_message(self.user, data)
        self.hud_queue.get().addCallback(self.dataFromTeeReceived)


class TeeToNetHackFactory(ClientFactory):
    protocol = TeeToNetHackProtocol

    def __init__(self, incoming_queue, outgoing_queue, hud_queue):
        self.incoming_queue = incoming_queue
        self.outgoing_queue = outgoing_queue
        self.hud_queue = hud_queue


### Testing shitz go after this point ###
def main():
    factory = Factory()
    factory.protocol = TeeFromClientProtocol
    reactor.listenTCP(12435, factory, interface="0.0.0.0")
    reactor.run()


if __name__ == "__main__":
    main()
