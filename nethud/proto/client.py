"""
An example client. Run simpleserv.py first before running this.
"""
from __future__ import unicode_literals

import json

from twisted.internet import reactor, protocol


# a client protocol

class NethackClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""

    method_calls = {}

    def connectionMade(self):
        self.factory.register_client(self)
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
        data = json.loads(data)
        for ret_key in data:
            if ret_key in self.method_calls:
                self.method_calls[ret_key](data[ret_key])
        self._run_next_command()

    def connectionLost(self, reason):
        print "Connection lost"
        self.factory.remove_client(self)

    def register_call(self, name, function):
        self.method_calls[name] = getattr(self, function)

    def _run_next_command(self):
        self.command_queue.get().addCallback(self.exec_command)

    def queue_command(self, command, **kw):
        self.command_queue.put((command, kw))

    def exec_command(self, command_tuple):
        self.send_message(command_tuple[0], **command_tuple[1])

    # Nethack Protocol Wrapper
    def send_message(self, command, **kw):
        data = json.dumps({command: kw})
        self.transport.write(data.encode('utf8'))
        print "Client says:", data

    # Nethack response methods


    def assume_y(self, _):
        self.send_message("yn", **{'return': 121})

    def store_current_games(self, gamelist):
        for game in gamelist['games']:
            self.games_queue.put(game['gameid'])
        self.games_queue.put(False)


class NethackFactory(protocol.ClientFactory):
    protocol = NethackClient
    clients = []

    def register_client(self, client):
        self.clients.append(client)

    def remove_client(self, client):
        self.clients.remove(client)

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()


def test(factory):
    if not factory.clients:
        reactor.callLater(2, test, factory)
        return
    client = factory.clients[0]


# this connects the protocol to a server runing on port 8000
def main():
    f = NethackFactory()
    reactor.connectTCP("games-ng.csh.rit.edu", 53421, f)
    reactor.callLater(0, test, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
