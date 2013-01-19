"""
An example client. Run simpleserv.py first before running this.
"""

import json

from twisted.internet import reactor, protocol


# a client protocol

class EchoClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""

    def connectionMade(self):
        self.send_message('auth', username='Qalthos', password='password')

    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print "Server said:", data

    def connectionLost(self, reason):
        print "Connection lost"

    # Nethack Protocol Wrapper
    def send_message(self, command, **kw):
        data = json.dumps(dict(command=kw))
        self.transport.write(data)


class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()


# this connects the protocol to a server runing on port 8000
def main():
    f = EchoFactory()
    reactor.connectTCP("games-ng.csh.rit.edu", 53421, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
