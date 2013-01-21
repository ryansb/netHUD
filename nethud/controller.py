from collections import defaultdict

try:
    import ultrajson as json
except ImportError:
    import json
from raven import Client
import sys
client = Client('http://b0d59e11ee8947fb975b7b99484e6975:8c0c35f542534da9a8f3fb46493bcd70@nethud.csh.rit.edu/2')


class LevelDetails(object):
    display = {}

    def update(self, display):
        for obj in display:
            try:
                key = obj.keys()[0]
                getattr(self, key)(obj[key])
            except:
                pass

    def get(self, key):
        return self.display.get(key, [])

    def list_items(self, items):
        if items['invent'] == 1:
            self.display['list_items'] = items['items']

    def update_screen(self, mapdelta):
        try:
            details = self.display['update_screen']
        except:
            self.display['update_screen'] = mapdelta['dbuf']
            return

        for col_index, col in enumerate(mapdelta):
            # 0: this column is empty; clear
            if col == 0:
                details[col_index] = 0
            # 1: nothing has changed since last update; ignore
            elif col == 1:
                continue
            # list: something has changed
            elif isinstance(col, list):
                # If there isn't a list here already, the whole thing is new
                if not isinstance(details[col_index], list):
                    details[col_index] = col
                    continue
                for row_index, cell in enumerate(col):
                    if cell == 0 or isinstance(cell, list):
                        # I think we can just drop it in, no need to check for
                        # 1s
                        details[col_index][row_index] = 0

        self.display['update_screen'] = details

    def update_status(self, statusdelta):
        try:
            status = self.display['update_status']
        except:
            self.display['update_status'] = statusdelta
            return

        for key in statusdelta.keys():
            status[key] = statusdelta[key]
        self.display['update_status'] = status


class Controller(object):
    users = {}
    cached_details = defaultdict(LevelDetails)
    detail_keys = [None] * 10

    @staticmethod
    def send_message(user, msg):
        data = json.loads(msg)
        if 'display' in data.keys():
            current = Controller.cached_details[user]
            current.update(data['display'])
            Controller.cached_details[user] = current
        if user in Controller.users:
            try:
                Controller.users[user](msg)
            except Exception as e:
                print e
                client.captureException(sys.exc_info())

    @staticmethod
    def connect_user(user, handle_function):
        Controller.users[user] = handle_function

    @staticmethod
    def disconnect_user(user):
        try:
            del Controller.users[user]
        except Exception as e:
            print e
            client.captureException(sys.exec_info())

    @staticmethod
    def store_legend(legend_data):
        Controller.detail_keys[2] = ['Traps'] + legend_data['traps']
        Controller.detail_keys[3] = ['Objects'] + legend_data['objects']
        Controller.detail_keys[5] = ['Monsters'] + legend_data['monsters']
