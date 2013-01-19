"""
An example client. Run simpleserv.py first before running this.
"""
from __future__ import unicode_literals

import json

from twisted.internet import reactor, protocol


# a client protocol

class NethackClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""

    def connectionMade(self):
        running = True
        self.send_message("auth", username="rossdylan", password="herpderp")
        self.send_message("start_game", alignment=0, gender=0, name="herpderp",
                          race=0, role=0)
        self.send_message("get_roles")
        self.send_message("exit_game", exit_type=2)
        #~ self.transport.loseConnection()

    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print "Server said:", data

    def connectionLost(self, reason):
        print "Connection lost"

    # Nethack Protocol Wrapper
    def send_message(self, command, **kw):
        data = json.dumps({command: kw})
        print "Client says:", data
        self.transport.write(data.encode('utf8'))


class NethackFactory(protocol.ClientFactory):
    protocol = NethackClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()


# this connects the protocol to a server runing on port 8000
def main():
    f = NethackFactory()
    reactor.connectTCP("games-ng.csh.rit.edu", 53421, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
