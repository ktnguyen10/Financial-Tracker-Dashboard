import calendar
import pandas as pd
from io import StringIO
from datetime import datetime
from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import login_manager as lm
from helpers import login_required
from financial_dashboard.dashboard.data_prep import gen_dataframe

main_data = pd.DataFrame
months_dict = {month: index for index, month in enumerate(calendar.month_name) if month}
years_list = [i for i in range(2022, 2025)]


def protected_dashviews(dashapp):
    for view_function in dashapp.server.view_functions:
        if view_function.startswith(dashapp.config['routes_pathname_prefix']):
            dashapp.server.view_functions[view_function] = login_required(dashapp.server.view_functions[view_function])


def register_dashapp(flask_app, curs):
    global main_data
    username = lm.get_current_user()

    # Create Plotly Dash dashboard
    app_dash = Dash(server=flask_app, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    routes_pathname_prefix='/dashboard/')
    # Get data
    data, overall_pie_user, overall_pie_cat = gen_dataframe(curs, username)
    data = data.drop_duplicates(subset=list(data.columns[data.columns != 'id']))
    main_data = data

    user_list = [x for x in list(data['user'].unique()) if isinstance(x, str)]
    user_list.append('all')

    app_dash.layout = dbc.Container([
        dcc.Location(id='url', refresh=True),

        dcc.Store(id='table_memory'),

        html.H1(username + " Financial Dashboard", style={'textAlign': 'center'}),

        html.A(html.Button("Go Home", id="go_home", n_clicks='0'), href='/'),
        html.A(html.Button("Refresh", id="refresh_data", n_clicks='0'), href='/dashboard'),

        html.H2("Overall Data by Category", style={'textAlign': 'center'}),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='cat_choice',
                    value=(list(data['custom_category'].unique())[0] if list(data['custom_category'].unique()) else ''),
                    clearable=False,
                    options=list(data['custom_category'].unique()))
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id='year_choice_1',
                    value=datetime.now().year,
                    clearable=False,
                    options=list(years_list))
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id='user_choice',
                    value=user_list[0],
                    clearable=False,
                    options=user_list)
            ], width=4),
        ], align='center'),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='category-by-month-bar', figure={})
            ], width=12),
        ]),

        html.Br(),

        dash_table.DataTable(id='category-statistics'),

        html.Br(),
        html.H2("Monthly Spending Summary", style={'textAlign': 'center'}),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='month_choice',
                    value=list(months_dict.keys())[datetime.now().month - 1],
                    clearable=False,
                    options=list(months_dict.keys()))
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id='year_choice_2',
                    value=datetime.now().year,
                    clearable=False,
                    options=list(years_list))
            ], width=4),
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='category-spend-pie', figure={})
            ], width=12, md=6),
            dbc.Col([
                dcc.Graph(id='spend-by-person-stacked', figure={})
            ], width=12, md=6)
        ], className='mt-4'),

        html.Br(),
        html.H2("Overall Spending", style={'textAlign': 'center'}),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='overall-pie-user', figure=overall_pie_user)
            ], width=12, md=6),
            dbc.Col([
                dcc.Graph(id='overall-pie-cat', figure=overall_pie_cat)
            ], width=12, md=6)
        ], className='mt-4'),

        html.Br(),
        html.H2("All Spend Table", style={'textAlign': 'center'}),
        dash_table.DataTable(id='all-spend-table'),

        html.Br(),
        html.H2("User Spend for Month and Year", style={'textAlign': 'center'}),
        dash_table.DataTable(id='user-summary-table'),

        html.Br(),
        html.H2("Spending Categories for Month and Year", style={'textAlign': 'center'}),
        dash_table.DataTable(id='cat-summary-table'),

        html.Div(id='last_update', style={'display': 'none'}),
        html.Div(id='return_call', style={'display': 'none'})
    ])

    init_callbacks(app_dash, curs)

    return app_dash.server


def init_callbacks(dashapp, curs):
    @dashapp.callback(
        [Output('last_update', 'children'),
         Output('overall-pie-user', 'figure'),
         Output('overall-pie-cat', 'figure')],
        Input('refresh_data', 'n_clicks')
    )
    def refresh_data(n):
        global main_data
        username = lm.get_current_user()
        data, overall_pie_user, overall_pie_cat = gen_dataframe(curs, username)
        data = data.drop_duplicates(subset=list(data.columns[data.columns != 'id']))
        main_data = data

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S"), overall_pie_user, overall_pie_cat

    @dashapp.callback(
        [Output('category-statistics', 'data'),
         Output('category-statistics', 'columns'),
         Output('category-by-month-bar', 'figure')],
        [Input('cat_choice', 'value'),
         Input('year_choice_1', 'value'),
         Input('user_choice', 'value')]
    )
    def category_statistics(selected_cat, selected_year, selected_user):
        global main_data
        data = main_data

        data['month'] = data['date'].dt.month
        data['month_name'] = data['month'].apply(lambda x: calendar.month_abbr[x])

        if selected_user == 'all':
            filtered_data = (data[(data['custom_category'] == selected_cat) & (data['date'].dt.year == selected_year)].
                             groupby(by=['month_name']).agg({'amount': 'sum'}))
            filtered_data.reset_index(inplace=True)
            ordered_months = [calendar.month_abbr[i + 1] for i in range(12)]
            filtered_data.index = pd.CategoricalIndex(filtered_data['month_name'], categories=ordered_months,
                                                      ordered=True)
            filtered_data = filtered_data.sort_index().reset_index(drop=True)
            bar_cat_by_month = px.bar(filtered_data, x='month_name', y='amount')
        else:
            filtered_data = (data[(data['custom_category'] == selected_cat) & (data['date'].dt.year == selected_year)].
                             groupby(by=['user', 'month_name']).agg({'amount': 'sum'}))
            filtered_data.reset_index(inplace=True)
            filtered_data = filtered_data[filtered_data['user'] == selected_user]
            ordered_months = [calendar.month_abbr[i + 1] for i in range(12)]
            filtered_data.index = pd.CategoricalIndex(filtered_data['month_name'], categories=ordered_months,
                                                      ordered=True)
            filtered_data = filtered_data.sort_index().reset_index(drop=True)
            bar_cat_by_month = px.bar(filtered_data, x='month_name', y='amount', color='user')

        agg_data = filtered_data['amount'].describe().reset_index()
        cols = [{'name': col, 'id': col} for col in agg_data.columns]
        table = agg_data.to_dict(orient='records')

        return table, cols, bar_cat_by_month

    @dashapp.callback(
        Output('return_call', 'children'),
        Input('go_home', 'n_clicks')
    )
    def go_home(n):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @dashapp.callback(
        [Output('category-spend-pie', 'figure'),
         Output('spend-by-person-stacked', 'figure'),
         Output('table_memory', 'data')],
        [Input('month_choice', 'value'),
         Input('year_choice_2', 'value')]
    )
    def monthly_data(selected_month, selected_year):
        global main_data
        data = main_data

        filtered_data = data[(data['date'].dt.month == months_dict[selected_month]) &
                             (data['date'].dt.year == selected_year) &
                             (data['custom_category'] != 'Payment')]

        agg_data = filtered_data.groupby(['custom_category']).agg({'amount': 'sum'})
        pie_monthly_cat = px.pie(agg_data.reset_index(), values='amount', names='custom_category')

        agg_data = filtered_data.groupby(['user', 'custom_category']).agg({'amount': 'sum'})
        bar_monthly_person = px.bar(agg_data.reset_index(), x='user', y='amount', color='custom_category')

        # Top spending categories
        top_spend_cats = agg_data.sort_values(['user', 'amount'], axis=0).reset_index().to_json()

        return pie_monthly_cat, bar_monthly_person, top_spend_cats

    @dashapp.callback(
        [Output('all-spend-table', 'data'),
         Output('all-spend-table', 'columns')],
        Input('table_memory', 'data')
    )
    def update_monthly_cat_spend(clean_data):
        agg_data = pd.read_json(StringIO(clean_data))
        cols = [{'name': col, 'id': col} for col in agg_data.columns]
        table = agg_data.to_dict(orient='records')
        return table, cols

    @dashapp.callback(
        [Output('user-summary-table', 'data'),
         Output('user-summary-table', 'columns')],
        Input('table_memory', 'data')
    )
    def update_summary_spend(clean_data):
        agg_data = pd.read_json(StringIO(clean_data))
        agg_data = agg_data.groupby(['user']).agg({'amount': 'sum'}).reset_index()
        cols = [{'name': col, 'id': col} for col in ['user', 'amount']]
        table = agg_data.to_dict(orient='records')
        return table, cols

    @dashapp.callback(
        [Output('cat-summary-table', 'data'),
         Output('cat-summary-table', 'columns')],
        Input('table_memory', 'data')
    )
    def update_summary_spend(clean_data):
        agg_data = pd.read_json(StringIO(clean_data))
        agg_data = agg_data.groupby(['custom_category']).agg({'amount': 'sum'}).reset_index()
        cols = [{'name': col, 'id': col} for col in ['custom_category', 'amount']]
        table = agg_data.to_dict(orient='records')
        return table, cols
