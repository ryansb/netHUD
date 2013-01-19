"""
An example client. Run simpleserv.py first before running this.
"""
from __future__ import unicode_literals

import json
from threading import Event

from twisted.internet import reactor, protocol, threads, defer

from nethud.dpqueue import DeferredPriorityQueue
from nethud.util.monst import lookup_monster
from nethud.util.objects import lookup_object


class NethackClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""

    method_calls = {}
    command_queue = DeferredPriorityQueue()
    games_queue = defer.DeferredQueue()
    monsters = {}
    items = {}
    data_buffer = ''

    def connectionMade(self):
        self.factory.register_client(self)
        self.register_call('display', 'display')
        self.register_call('display_objects', 'objects')
        self._run_next_command()

    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        #~ print "Server said:", data
        if self.data_buffer:
            data = self.data_buffer + data
            self.data_buffer = ''
        try:
            data = json.loads(data)
        except ValueError:
            # We probably just didn't get all of it
            self.data_buffer = data
            return
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

    def queue_command(self, command, priority=10, **kw):
        self.command_queue.put(priority, (command, kw))

    def exec_command(self, command_tuple):
        self.send_message(command_tuple[0], **command_tuple[1])

    # Nethack Protocol Wrapper
    def send_message(self, command, **kw):
        data = json.dumps({command: kw})
        self.transport.write(data.encode('utf8'))
        print "Client says:", data

    # Nethack response methods
    def display(self, display_data):
        for packet in display_data:
            if packet.get('update_screen'):
                for x_index, col in enumerate(packet['update_screen']['dbuf']):
                    if isinstance(col, list):
                        for y_index, cell in enumerate(col):
                            if isinstance(cell, list):
                                coords = "{0},{1}".format(x_index, y_index)
                                self.items[coords] = cell[3]
                                self.monsters[coords] = cell[5]
            if packet.get('print_message_nonblocking'):
                print packet['print_message_nonblocking']['msg']

        for key, item in self.items.items():
            if item == 0:
                del self.items[key]
            else:
                print "There is a {0} at {1}".format(lookup_object(item), key)
        for key, monster in self.monsters.items():
            if monster == 0:
                del self.monsters[key]
            else:
                print "There is a {0} at {1}".format(lookup_monster(monster), key)

    def objects(self, objects):
        for item in objects['items']:
            print item[0]

    def assume_y(self, _):
        self.queue_command("yn", priority=0, **{'return': 121})

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

    # Force yn prompts to respond with y
    client.register_call('yn', 'assume_y')
    client.register_call('list_games', 'store_current_games')

    # Create a game, then exit.
    client.queue_command("auth", username="Qalthos", password="password")
    client.queue_command("list_games", completed=0, limit=0, show_all=1)

    def restore_or_start(gameid):
        if gameid:
            client.queue_command("restore_game", gameid=gameid)
        else:
            client.queue_command("start_game", alignment=0, gender=1,
                                 name="herpderp", race=0, role=0, mode=0)
        client.queue_command("get_drawing_info")
        client.queue_command("exit_game", exit_type=0)
        client.queue_command("shutdown")

    client.games_queue.get().addCallback(restore_or_start)


# this connects the protocol to a server runing on port 8000
def main():
    f = NethackFactory()
    reactor.connectTCP("games-ng.csh.rit.edu", 53421, f)
    reactor.callLater(0, test, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
