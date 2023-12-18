from flask import Flask


def init_app():
    app = Flask(__name__, instance_relative_config=False)

    with app.app_context():
        from financial_dashboard import routes

        # Import Dash app
        from financial_dashboard.dashboard import register_dashapp
        print(routes.curs)

        app = register_dashapp(app, routes.curs)

        return app
