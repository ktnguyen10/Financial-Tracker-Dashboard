import calendar
import pandas as pd
from io import StringIO
from datetime import datetime
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from helpers import login_required
from dash import dash_table
import plotly.express as px


months_dict = {month: index for index, month in enumerate(calendar.month_name) if month}
years_list = [i for i in range(2022, 2024)]


def query_transactions(curs, username):
    curs.execute("SELECT * FROM transactions WHERE user_id LIKE (?)", (username,))
    data = curs.fetchall()
    # Data is returned as a dictionary
    return data


def create_dash_app(flask_app, curs, username):
    data = pd.DataFrame.from_dict(query_transactions(curs, username))
    if len(data) == 0:
        return None
    data['date'] = data['transaction_date'].apply(lambda x: datetime.strptime(x, '%m/%d/%y'))
    data['amount'] = data['amount'].apply(lambda x: -x)
    data['category'] = data['category'].apply(lambda x: 'Shopping' if x == 'Normal' else x)

    print(data.head())

    # Create Plotly Dash dashboard
    app_dash = Dash(server=flask_app, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    routes_pathname_prefix='/dashboard/')

    for view_function in app_dash.server.view_functions:
        if view_function.startswith(app_dash.config.url_base_pathname):
            app_dash.server.view_functions[view_function] = login_required(app_dash.server.view_functions[view_function])

    app_dash.layout = dbc.Container([
        dcc.Store(id='table_memory'),

        html.H1("Kevin Financial Dashboard", style={'textAlign': 'center'}),

        html.H2("Monthly Spending Summary", style={'textAlign': 'center'}),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='month_choice',
                    value=list(months_dict.keys())[datetime.now().month - 1],
                    clearable=False,
                    options=list(months_dict.keys()))
            ], width=4)
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='category-spend-pie', figure={})
            ], width=12, md=6),
            dbc.Col([
                dcc.Graph(id='spend-by-person-stacked', figure={})
            ], width=12, md=6)
        ], className='mt-4'),

        dash_table.DataTable(id='top-spend-table'),

        html.H2("Overall Spending"),

        # dbc.Row([
        #     dbc.Col([
        #         dcc.Graph(id='overall-pie-user', figure=overall_pie_user)
        #     ], width=12, md=6),
        #     dbc.Col([
        #         dcc.Graph(id='overall-pie-cat', figure=overall_pie_cat)
        #     ], width=12, md=6)
        # ], className='mt-4'),
    ])

    # with flask_app.app_context():
    #     app_dash.layout = layout
    #     register_callbacks(app_dash, data)

    return app_dash.server


def init_callbacks(dashapp, data):
    @dashapp.callback(
        [Output('category-spend-pie', 'figure'),
         Output('spend-by-person-stacked', 'figure'),
         Output('table_memory', 'data')],
        Input('month_choice', 'value')
    )
    def monthly_data(selected_month):
        filtered_data = data[(data['Date'].dt.month == months_dict[selected_month]) &
                             (data['Custom Category'] != 'Payment')]

        agg_data = filtered_data.groupby(['Custom Category']).agg({'Amount': 'sum'})
        pie_monthly_cat = px.pie(agg_data.reset_index(), values='Amount', names='Custom Category')

        agg_data = filtered_data.groupby(['User', 'Custom Category']).agg({'Amount': 'sum'})
        bar_monthly_person = px.bar(agg_data.reset_index(), x='User', y='Amount', color='Custom Category')

        # Top spending categories
        top_spend_cats = agg_data.sort_values(['User', 'Amount'], axis=0).reset_index().to_json()

        return pie_monthly_cat, bar_monthly_person, top_spend_cats

    @dashapp.callback(
        [Output('top-spend-table', 'data'),
         Output('top-spend-table', 'columns')],
        Input('table_memory', 'data')
    )
    def update_monthly_cat_spend(clean_data):
        agg_data = pd.read_json(StringIO(clean_data))
        cols = [{'name': col, 'id': col} for col in agg_data.columns]
        table = agg_data.to_dict(orient='records')
        return table, cols
