try:
    import ultrajson as json
except ImportError:
    import json
from raven import Client
from sys import exec_info
client = Client('http://b0d59e11ee8947fb975b7b99484e6975:8c0c35f542534da9a8f3fb46493bcd70@nethud.csh.rit.edu/2')


class Controller(object):
    users = {}
    cached_details = {}
    detail_keys = [None] * 10

    @staticmethod
    def send_message(user, msg):
        if user in Controller.users:
            if Controller.cached_details.get(user):
                Controller.users[user](Controller.cached_details.get(user))
            try:
                Controller.users[user](msg)
            except Exception as e:
                print e
                client.captureException(exec_info())
        else:
            data = json.loads(msg)
            if 'display' in data.keys():
                current = Controller.cached_details.get(user, list())
                for index, update_dict in enumerate(data['display']):
                    current[index].update(update_dict)
                Controller.cached_details[user] = current

    @staticmethod
    def connect_user(user, handle_function):
        Controller.users[user] = handle_function
        client.captureMessage("{} has connected".format(user))

    @staticmethod
    def disconnect_user(user):
        try:
            del Controller.users[user]
        except Exception as e:
            print e
            client.captureException(exec_info())

    @staticmethod
    def store_legend(legend_data):
        Controller.detail_keys[2] = ['Traps'] + legend_data['traps']
        Controller.detail_keys[3] = ['Objects'] + legend_data['objects']
        Controller.detail_keys[5] = ['Monsters'] + legend_data['monsters']
