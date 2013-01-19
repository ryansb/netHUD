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
        self.command_queue = []
        self.command_queue.append(("auth", dict(username="rossdylan",
                                                password="herpderp")))
        # gender = [male, female, neuter]
        #~ self.command_queue.append(("get_pl_prompt", dict(align=-1, gend=0,
                                                      #~ race=-1, role=-1)))
        self.command_queue.append(("start_game", dict(alignment=0, gender=1,
                                                      name="herpderp", race=0,
                                                      role=0, mode=2)))
        #~ self.command_queue.append(("list_games", dict(completed=False, limit=5, show_all=True)))
        #~ self.command_queue.append(("get_roles", dict()))
        #~ self.command_queue.append(("exit_game", dict(exit_type=2)))

        self.exec_next_command()

    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print "Server said:", data
        if self.command_queue:
            self.exec_next_command()
        else:
            self.transport.loseConnection()

    def connectionLost(self, reason):
        print "Connection lost"

    # Nethack Protocol Wrapper
    def exec_next_command(self):
        comm = self.command_queue.pop(0)
        self.send_message(comm[0], **comm[1])

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
