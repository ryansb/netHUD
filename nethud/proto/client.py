"""
An example client. Run simpleserv.py first before running this.
"""
from __future__ import unicode_literals, print_function
from collections import defaultdict

import json

from twisted.internet import reactor, protocol, threads, defer

from nethud.dpqueue import DeferredPriorityQueue


class NethackClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""

    # Default user handler prints to terminal
    users = {'': print}
    method_calls = {}
    command_queue = DeferredPriorityQueue()
    games_queue = defer.DeferredQueue()
    details = []
    detail_keys = [None] * 10

    data_buffer = ''

    def connectionMade(self):
        self.factory.register_client(self)
        self.register_call('display', 'display')
        self.register_call('get_drawing_info', 'set_info')
        self.register_call('display_objects', 'objects')
        self._run_next_command()

    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        #~ print("Server said:", data)
        try:
            user, data = data
        except ValueError:
            user = ''

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
                self.method_calls[ret_key](data[ret_key], user)
        self._run_next_command()

    def connectionLost(self, reason):
        print("Connection lost")
        self.factory.remove_client(self)

    def register_call(self, name, function):
        self.method_calls[name] = getattr(self, function)

    def _run_next_command(self):
        """
        Starts the DeferredQueue running.  This should only need to be run
        manually once, then automatically at the end of dataReceived.
        """
        self.command_queue.get().addCallback(self.exec_command)

    def queue_command(self, command, user='', priority=10, **kw):
        self.command_queue.put(priority, (user, command, kw))

    def exec_command(self, command_tuple):
        self.send_message(command_tuple[0], command_tuple[1], **command_tuple[2])

    # Register/deregister Telnet sinks per user
    def assoc_client(self, uname, telnet_protocol):
        self.users[uname] = telnet_protocol.sendLine

    def deassoc_client(self, uname):
        del self.users[uname]

    # Nethack Protocol Wrapper
    def send_message(self, user, command, **kw):
        #TODO: user?
        data = json.dumps({command: kw})
        self.transport.write(data.encode('utf8'))
        #~ print("Client says:", data)

    # Nethack response methods
    def set_info(self, keys, _):
        self.detail_keys[2] = ['Traps'] + keys['traps']
        self.detail_keys[3] = ['Objects'] + keys['objects']
        self.detail_keys[5] = ['Monsters'] + keys['monsters']

    def display(self, display_data, user):
        status_line = ''
        messages = []
        inventory = []
        pois = defaultdict(list)

        for packet in display_data:
            if packet.get('update_status'):
                status = packet['update_status']
                status_line = "{0} {1} has {2} gold, {3} xp, and {4}/{5} hp " \
                    .format(*map(lambda x: status.get(x),
                    ['rank', 'plname', 'gold', 'xp', 'hp', 'hpmax']))
            if packet.get('update_screen'):
                for x_index, col in enumerate(packet['update_screen']['dbuf']):
                    if x_index >= len(self.details):
                        self.details.append(col)
                        continue
                    elif isinstance(col, list):
                        for y_index, cell in enumerate(col):
                            if isinstance(cell, list) or cell == 0:
                                self.details[x_index][y_index] = cell
                    elif col == 0:
                        self.details[x_index] = col
            if packet.get('print_message'):
                messages.append(packet['print_message']['msg'])
            if packet.get('print_message_nonblocking'):
                messages.append(packet['print_message_nonblocking']['msg'])
            if packet.get('raw_print'):
                messages.append(packet['raw_print'])
            if packet.get('list_items'):
                inventory = self.objects(packet['list_items'])

        for x_index, col in enumerate(self.details):
            if isinstance(col, list):
                for y_index, cell in enumerate(col):
                    if isinstance(cell, list):
                        for index, key_type in enumerate(self.detail_keys):
                            if key_type and cell[index]:
                                char = chr(key_type[cell[index]][1])
                                thing = key_type[cell[index]][0]
                                pois[key_type[0]].append("There is a {0} ({1}) at {2},{3}"
                                    .format(char, thing, x_index, y_index))
        self.fancy_display(user, status_line, messages, inventory, pois)

    def objects(self, objects, *_):
        inv = ["Your inventory contains:"]
        for item in objects['items']:
            inv.append(item[0])
        return inv

    def assume_y(self, *_):
        self.queue_command("yn", priority=0, **{'return': 121})

    def store_current_games(self, gamelist, user):
        for game in gamelist['games']:
            if game['status'] < 0:
                continue
            self.games_queue.put(game['gameid'])
        self.games_queue.put(False)

    def fancy_display(self, user, status, messages, inventory, pois):
        """Overelaborate display for status."""
        out_func = self.users[user]
        out_func('#' + '=' * 36 + "STATUS" + "=" * 36 + '#')
        out_func('|' + status + ' ' * (78 - len(status)) + '|')
        out_func('#' + '=' * 15 + "MESSAGES" + "=" * 15 + '#' +
                 '#' + '=' * 15 + "INVENTORY" + "=" * 14 + '#')
        left = []
        right = []
        for line in messages:
            while len(line) > 38:
                left.append(line[:38])
                line = line[38:]
            left.append(line)
            left.append("=" * 16 + "NEARBY" + "=" * 16)
        for type_ in pois:
            left.append("--" + type_)
            for line in pois[type_]:
                while len(line) > 38:
                    left.append(line[:38])
                    line = line[38:]
                left.append(line)
        for line in inventory:
            while len(line) > 38:
                right.append(line[:38])
                line = line[38:]
            right.append(line)
        if len(left) > len(right):
            right.extend([''] * (len(left) - len(right)))
        elif len(left) < len(right):
            left.extend([''] * (len(right) - len(left)))
        for index in range(len(left)):
            min_r = min(len(right[index]), 38)
            out_func("|" + left[index] + " " * (38 - len(left[index])) + "|" +
                     "|" + right[index] + " " * (38 - len(right[index])) + "|")
        out_func('#' + '=' * 78 + '#')


class NethackFactory(protocol.ClientFactory):
    protocol = NethackClient
    client = None

    def register_client(self, client):
        client = client

    def remove_client(self, client):
        client = None

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed - goodbye!")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost - goodbye!")
        reactor.stop()


def test(factory):
    if not factory.client:
        reactor.callLater(2, test, factory)
        return
    client = factory.client

    # Force yn prompts to respond with y
    client.register_call('yn', 'assume_y')
    client.register_call('list_games', 'store_current_games')

    # Create a game, then exit.
    client.queue_command("auth", username="Qalthos", password="password")
    client.queue_command("get_drawing_info")
    client.queue_command("list_games", completed=0, limit=0, show_all=0)

    def restore_or_start(gameid):
        if gameid:
            client.queue_command("restore_game", user='', gameid=gameid)
        else:
            client.queue_command("start_game", user='', alignment=0, gender=0,
                                 name="herpderp", race=0, role=0, mode=0)

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
