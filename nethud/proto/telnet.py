from __future__ import print_function
from collections import defaultdict

try:
    import ultrajson as json
except:
    import json

from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from nethud.controller import Controller


class TelnetConnection(LineReceiver):
    def __init__(self, users):
        self.width = 80
        self.users = users
        self.uname = ''
        self.auth = False
        self.data_buffer = ''
        self.input_handlers = {'display': self.display,
                               'display_objects': self.objects}

    # Twistedy methods!
    def connectionLost(self, reason):
        Controller.disconnect_user(self.uname)
        if self.uname in self.users:
            del self.users[self.uname]
        self.uname = ''
        print(reason)

    def lineReceived(self, line):
        msg_split = line.split()
        if msg_split[0] == 'AUTH':
            if len(msg_split) != 2:
                self.sendLine("ERR 406 Invalid Parameters.")
                return
            self.handle_auth(msg_split[1])
        elif msg_split[0] == 'WIDTH':
            try:
                self.width = int(msg_split[1])
            except:
                self.sendLine("ERR 406 Invalid Parameters.")
        elif msg_split[0] == 'QUIT':
            self.transport.loseConnection()
        else:
            self.sendLine("ERR 452 Invalid Command")

    # Bookkeeping methods
    def handle_auth(self, uname):
        self.users[uname] = self
        self.uname = uname
        Controller.connect_user(uname, self.handle_data)
        self.auth = True

    def handle_data(self, json_data):
        if self.data_buffer:
            data = self.data_buffer + json_data
            self.data_buffer = ''
        try:
            data = json.loads(json_data)
        except ValueError:
            # We probably just didn't get all of it
            self.data_buffer = json_data
            return

        for ret_key in data:
            if ret_key in self.input_handlers:
                self.input_handlers[ret_key](data[ret_key])

    # Methods  to actually do something about the Nethack data
    def display(self, display_data):
        """
        This interprets `display` objects and tries to pass that information
        on to the user.
        """
        cache = Controller.cached_details[self.uname]
        status = cache.get('update_status')
        details = cache.get('update_screen')
        inventory = cache.get('list_items')
        messages = []
        pois = defaultdict(list)

        for packet in display_data:
            if packet.get('print_message'):
                messages.append(packet['print_message']['msg'])
            #~ if packet.get('print_message_nonblocking'):
                #~ messages.append(packet['print_message_nonblocking']['msg'])
            if packet.get('raw_print'):
                messages.append(packet['raw_print'])
            if packet.get('list_items') and packet['list_items']['invent'] == 0:
                for item in packet['list_items']['items']:
                    messages.append(item[0])

        status_line = "{0} {1} has {2} gold, {3} xp, and {4}/{5} hp " \
            .format(*map(lambda x: status.get(x),
            ['rank', 'plname', 'gold', 'xp', 'hp', 'hpmax']))

        for x_index, col in enumerate(details):
            if isinstance(col, list):
                for y_index, cell in enumerate(col):
                    if isinstance(cell, list):
                        for index, key_type in enumerate(Controller.detail_keys):
                            if key_type and cell[index]:
                                char = chr(key_type[cell[index]][1])
                                thing = key_type[cell[index]][0]
                                pois[key_type[0]].append("There is a {0} ({1}) at {2},{3}"
                                    .format(char, thing, x_index, y_index))
        self.fancy_display(status_line, messages, inventory, pois)

    def objects(self, objects):
        """
        Method to handle inventory.  This gets called from a few spots, so it
        gets it's own method.
        """

        inv = ["Your inventory contains:"]
        for item in objects['items']:
            inv.append(item[0])
        return inv

    def fancy_display(self, status, messages, inventory, pois):
        """Overelaborate display for status."""
        output = []
        padding = self.width - 2
        output.extend(self.make_string('STATUS', '#', '=', padding, True))
        output.extend(self.make_string(status, '|', ' ', padding))

        if self.width >= 90:
            # Try having three columns
            padding = padding / 3
        elif self.width >= 60:
            # We'll be using two columns
            padding = padding / 2

        mdisplay = self.make_string("MESSAGES", '#', '=', padding, True)
        for line in messages:
            mdisplay.extend(self.make_string(line, '|', ' ', padding))

        ndisplay = self.make_string('NEARBY', '#', '=', padding, True)
        for type_ in pois:
            ndisplay.extend(self.make_string("--" + type_, '|', ' ', padding))
            for line in pois[type_]:
                ndisplay.extend(self.make_string(line, '|', ' ', padding))

        idisplay = self.make_string('INVENTORY', '#', '=', padding, True)
        for line in inventory:
            if line[2] == 1:
                line = "{0}: {1} ({2})".format(chr(line[8]), chr(line[9]), line[0])
            else:
                line = ' {0}'.format(line[0])
            idisplay.extend(self.make_string(line, '|', ' ', padding))

        if self.width >= 90:
            # Three column display
            #TODO
            pass
        elif self.width >= 60:
            # Two column display
            left = mdisplay + ndisplay
            right = idisplay
            if len(left) > len(right):
                difference = len(left) - len(right)
                right.extend(self.make_string('', '|', ' ', padding) * difference)
            elif len(left) < len(right):
                difference = len(right) - len(left)
                left.extend(self.make_string('', '|', ' ', padding) * difference)
            for index in range(len(left)):
                output.append(left[index] + right[index])
        else:
            output.extend(mdisplay)
            output.extend(ndisplay)
            output.extend(idisplay)

        # But first, make sure the screen is clear!
        for i in range(30):
            self.sendLine('')
        for line in output:
            self.sendLine(line.encode('utf8'))

    def make_string(self, string, sidechar, padchar, maxwidth, center=False):
        output = []
        while len(string) > maxwidth:
            output.append(sidechar + string[:maxwidth] + sidechar)
            string = string[maxwidth:]
        if center:
            offset = (maxwidth - len(string)) / 2
            output.append(sidechar + (padchar * int(offset)) + string +
                          (padchar * int(offset + .5)) + sidechar)
        else:
            offset = maxwidth - len(string)
            output.append(sidechar + string + (padchar * offset) + sidechar)
        return output


class TelnetFactory(protocol.Factory):
    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return TelnetConnection(users=self.users)
