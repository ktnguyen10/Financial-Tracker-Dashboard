import calendar
import pandas as pd
from io import StringIO
from datetime import datetime
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from helpers import login_required
from dash import dash_table
from financial_dashboard.dashboard.data_prep import gen_dataframe
import plotly.express as px

months_dict = {month: index for index, month in enumerate(calendar.month_name) if month}
years_list = [i for i in range(2022, 2024)]


def protected_dashviews(dashapp):
    for view_function in dashapp.server.view_functions:
        if view_function.startswith(dashapp.config['routes_pathname_prefix']):
            dashapp.server.view_functions[view_function] = login_required(dashapp.server.view_functions[view_function])


def register_dashapp(flask_app, curs):
    from flask import session
    # Create Plotly Dash dashboard
    app_dash = Dash(server=flask_app, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    routes_pathname_prefix='/dashboard/')
    # Get data
    data, overall_pie_user, overall_pie_cat = gen_dataframe(curs, 'ktnguyen')

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

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='overall-pie-user', figure=overall_pie_user)
            ], width=12, md=6),
            dbc.Col([
                dcc.Graph(id='overall-pie-cat', figure=overall_pie_cat)
            ], width=12, md=6)
        ], className='mt-4'),
    ])

    init_callbacks(app_dash, data)

    return app_dash.server


def init_callbacks(dashapp, data):
    @dashapp.callback(
        [Output('category-spend-pie', 'figure'),
         Output('spend-by-person-stacked', 'figure'),
         Output('table_memory', 'data')],
        Input('month_choice', 'value')
    )
    def monthly_data(selected_month):
        filtered_data = data[(data['date'].dt.month == months_dict[selected_month]) &
                             (data['custom_category'] != 'Payment')]

        agg_data = filtered_data.groupby(['custom_category']).agg({'amount': 'sum'})
        pie_monthly_cat = px.pie(agg_data.reset_index(), values='amount', names='custom_category')

        agg_data = filtered_data.groupby(['user', 'custom_category']).agg({'amount': 'sum'})
        bar_monthly_person = px.bar(agg_data.reset_index(), x='user', y='amount', color='custom_category')

        # Top spending categories
        top_spend_cats = agg_data.sort_values(['user', 'amount'], axis=0).reset_index().to_json()

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
