from __future__ import unicode_literals
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientFactory, Factory
from nethud.controller import Controller

try:
    import ultrajson as json
except:
    import json

"""
tee.py
nethud.proto.tee

tee.py acts kinda like a tee and copies all data going acrossed a connection
between the a nethack client and the nethack server. It will do a tiny bit of
processing to add a username to every message copied and sent through the tee


[Nethack Server]
    ----
    |  |
    |  |_______
    |   _______| [NetHUD] (NOTE: the NetHUD bit is replacable)
    |  |
    |  |
    ----
[Nethack Client]


NOTE: This is heavily inspired by https://gist.github.com/1878983
"""



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
        # This factory is used to spin up connections to the actual nethack
        # server

        hudToController = TeeToHUDController(self.hud_queue)
        # this obeject is used to forward all of our messages in the hud_queue
        # out of the telnet server
        reactor.connectTCP("games-ng.csh.rit.edu", 53421, toNetHackFactory)

    def dataFromNetHack(self, data):
        """Data returned from the nethack server"""
        self.transport.write(data)
        self.outgoing_queue.get().addCallback(self.dataFromNetHack)

    def dataReceived(self, data):
        """
        Data from the nethack client
        We should only need to send the auth data to the hud all other client
        data may be irrelevent
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
        self.data_buffer = ""
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
        if self.data_buffer:
            data = self.data_buffer + data
            self.data_buffer = ''
        try:
            data = json.loads(data)
        except ValueError:
            # We probably just didn't get all of it
            self.data_buffer = data
            return

        self.outgoing_queue.put(json.dumps(data))
        jData = data
        if "auth" in jData and not self.authPacket:
            self.authPacket = jData
        elif "auth" in jData and self.authPacket:
            self.authPacket.update(jData['auth'])
            self.hud_queue.put(json.dumps(self.authPacket))
        else:
            self.hud_queue.put(json.dumps(data))


class TeeToHUDController(object):
    """
    This class is hooked in to a deferred queue which gets messages from the
    client and server
    and uses controller.send_msg to push them out
    """
    def __init__(self, hud_queue):
        self.hud_queue = hud_queue
        self.hud_queue.get().addCallback(self.dataFromTeeReceived)
        self.user = ""

    def dataFromTeeReceived(self, data):
        jData = json.loads(data)
        if "auth" in jData:
            if 'username' in jData['auth']:
                self.user = jData['auth']['username']
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
