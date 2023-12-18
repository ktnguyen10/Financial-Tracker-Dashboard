import shelve


def get_current_user():
    with shelve.open("credentials") as shelve_file:
        try:
            username = str(shelve_file["username"])
        except KeyError:
            username = 'no_login'

    return username


def store_current_user(user_id):
    with shelve.open("credentials") as shelve_file:
        if user_id == '':
            shelve_file['username'] = 'no_login'
        else:
            shelve_file['username'] = user_id
    return 1

