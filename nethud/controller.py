try:
    import ultrajson as json
except ImportError:
    import json


class Controller(object):
    users = {}
    cached_details = {}
    detail_keys = [None] * 10

    @staticmethod
    def send_message(user, msg):
        if user in Controller.users:
            if Controller.cached_details.get(user):
                Controller.users[user](Controller.cached_details.get(user))
            Controller.users[user](msg)
        else:
            data = json.loads(msg)
            if 'display' in data.keys():
                current = Controller.cached_details.get(user, dict())
                for key in data['display']:
                    current[key].update(data['display'][key])
                Controller.cached_details[user] = current

    @staticmethod
    def connect_user(user, handle_function):
        Controller.users[user] = handle_function

    @staticmethod
    def disconnect_user(user):
        del Controller.users[user]

    @staticmethod
    def store_legend(legend_data):
        Controller.detail_keys[2] = ['Traps'] + legend_data['traps']
        Controller.detail_keys[3] = ['Objects'] + legend_data['objects']
        Controller.detail_keys[5] = ['Monsters'] + legend_data['monsters']
