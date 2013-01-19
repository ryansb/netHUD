from __future__ import print_function

from twisted.internet import reactor, protocol, threads, defer
from twisted.protocols.basic import LineReceiver

from nethud.proto.client import NethackFactory


class TelnetConnection(LineReceiver):
    def __init__(self, users):
        self.users = users
        self.uname = ''

    def connectionLost(self, reason):
        if NethackFactory.client:
            NethackFactory.client.deassoc_client(self.uname)
        if self.user.user_name in self.users:
            del self.users[self.user.user_name]
        self.uname = ''
        print(reason)

    def lineReceived(self, line):
        msg_split = line.split()
        if msg_split[0] == 'AUTH':
            if len(msg_split) != 2:
                self.sendLine("ERR 406 Invalid Parameters.")
                return
            self.handle_auth(msg_split[1])
        elif msg_split[0] == 'QUIT':
            self.loseConnection()
        else:
            self.sendLine("ERR 452 Invalid Command")

    def handle_auth(uname):
        self.users[uname] = self
        self.uname = uname
        if NethackFactory.client:
            NethackFactory.client.assoc_client(uname, self)



def TelnetFactory(protocol.Factory):
    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return TelnetConnection(users = self.users)
