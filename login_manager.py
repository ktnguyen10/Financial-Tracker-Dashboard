import shelve


class LoginManager:
    def __init__(self):
        self.current_username = ''

    def get_current_user(self):
        if self.current_username != '':
            return self.current_username
        else:
            with shelve.open("credentials") as shelve_file:
                try:
                    username = str(shelve_file["username"])
                except KeyError:
                    username = 'no_login'
            return username

    def store_current_user(self, test_user_id):
        with shelve.open("credentials") as shelve_file:
            if test_user_id == '':
                shelve_file['username'] = 'no_login'
            else:
                shelve_file['username'] = test_user_id
                self.current_username = test_user_id
        return 1

