from flask import Flask
import shelve


def init_app():
    app = Flask(__name__, instance_relative_config=False)

    with app.app_context():
        from financial_dashboard import routes

        # Import Dash app
        from financial_dashboard.dashboard import register_dashapp
        print(routes.curs)

        with shelve.open("credentials") as shelve_file:
            try:
                username = str(shelve_file["username"])
            except KeyError:
                username = 'no_login'

        app = register_dashapp(app, routes.curs, username)

        return app
