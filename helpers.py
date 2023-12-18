import login_manager as lm
from functools import wraps
from flask import redirect, session


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = lm.get_current_user()
        if session.get("user_id") is None:
            return redirect("/login")
        elif current_user == 'no_login':
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
