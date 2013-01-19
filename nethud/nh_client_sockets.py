import json
import socket


def createMsg(cmd, **kwargs):
    return json.dumps({cmd: kwargs})


def connect():
    s = socket.socket()
    s.connect(("games-ng.csh.rit.edu", 53421))
    return s

def main():
    sock = connect()
    authMsg = createMsg("auth", user="rossdylan", password="herpderp")
    sock.send(authMsg)
    print sock.recv(1024)

    sock = connect()
    regMsg = createMsg("register", user="rossdylan", password="herpderp")
    sock.send(regMsg)
    print sock.recv(1024)


if __name__ == "__main__":
    main()
