class Controller(object):
    users = {}
    detail_keys = [None] * 10

    @staticmethod
    def send_message(user, msg):
        if user in Controller.users:
            Controller.users[user](msg)

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