import dash_bootstrap_components as dbc
import plotly.express as px
from login_manager import LoginManager
import pandas as pd
import calendar
from financial_dashboard.dashboard.data_cleanup import gen_dataframe, plot_sankey
from dash import Dash, html, dcc, Input, Output, dash_table
from helpers import login_required
from datetime import datetime
from io import StringIO


class DashBoard:
    def __init__(self, flask_app, curs):
        self.data = pd.DataFrame
        self.income_data = pd.DataFrame
        self.months_dict = {month: index for index, month in enumerate(calendar.month_name) if month}
        self.years_list = [i for i in range(2022, 2025)]
        self.flask_app = flask_app
        self.dash_app = None
        self.curs = curs

    def protected_dashviews(self):
        dashapp = self.dash_app
        for view_function in dashapp.server.view_functions:
            if view_function.startswith(dashapp.config['url_base_pathname']):
                dashapp.server.view_functions[view_function] = login_required(dashapp.server.view_functions[view_function])

    def register_layout(self):
        lm = LoginManager()
        username = lm.get_current_user()
        data, income, overall_pie_user, overall_pie_cat = gen_dataframe(self.curs, username)
        self.data = data
        self.income_data = income

        user_list = [x for x in list(data['user'].unique()) if isinstance(x, str)]
        user_list.append('all')

        layout = html.Div([
            dcc.Location(id='url', refresh=True),

            dcc.Store(id='table_memory'),

            html.H1(username + " Financial Dashboard", style={'textAlign': 'center'}),

            html.A(html.Button("Go Home", id="go_home", n_clicks='0'), href='/'),
            html.A(html.Button("Refresh", id="refresh_data", n_clicks='0'), href='/dashboard'),

            html.H2("Annual Spending by Category", style={'textAlign': 'center'}),
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
                        options=list(self.years_list))
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
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='annual-breakdown-sankey', figure={})
                ], width=6)
            ], align='center'),

            dbc.Row([
                dbc.Col([
                    dash_table.DataTable(id='category-statistics')
                ], width=3),
            ], align='center'),

            html.Br(),
            html.H2("Monthly Spending Summary", style={'textAlign': 'center'}),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='month_choice',
                        value=list(self.months_dict.keys())[datetime.now().month - 1],
                        clearable=False,
                        options=list(self.months_dict.keys()))
                ], width=4),
                dbc.Col([
                    dcc.Dropdown(
                        id='year_choice_2',
                        value=datetime.now().year,
                        clearable=False,
                        options=list(self.years_list))
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
            html.Br(),

            html.Div(id='last_update', style={'display': 'none'}),
            html.Div(id='return_call', style={'display': 'none'})
        ], style={'margin': '10px 20px'})
        return layout

    def register_dashapp(self):
        # Create Plotly Dash dashboard
        dash_app = Dash(__name__, server=self.flask_app, external_stylesheets=[dbc.themes.BOOTSTRAP],
                        url_base_pathname='/dashboard/')

        layout = self.register_layout()
        dash_app.layout = layout
        self.init_callbacks(dash_app)
        self.dash_app = dash_app

        return dash_app

    def init_callbacks(self, dashapp):
        @dashapp.callback(
            [Output('last_update', 'children'),
             Output('overall-pie-user', 'figure'),
             Output('overall-pie-cat', 'figure')],
            Input('refresh_data', 'n_clicks'),
            prevent_initial_call=True
        )
        def refresh_data(n):
            lm = LoginManager()
            username = lm.get_current_user()
            data, income, overall_pie_user, overall_pie_cat = gen_dataframe(self.curs, username)

            return datetime.now().strftime("%Y-%m-%d %H:%M:%S"), overall_pie_user, overall_pie_cat

        @dashapp.callback(
            [Output('category-statistics', 'data'),
             Output('category-statistics', 'columns'),
             Output('category-by-month-bar', 'figure'),
             Output('annual-breakdown-sankey', 'figure')],
            [Input('cat_choice', 'value'),
             Input('year_choice_1', 'value'),
             Input('user_choice', 'value')]
        )
        def category_statistics(selected_cat, selected_year, selected_user):
            data = self.data
            income = self.income_data

            # Sankey
            annual_breakdown_sankey = plot_sankey(data, income, selected_year)

            data['month'] = data['date'].dt.month
            data['month_name'] = data['month'].apply(lambda m: calendar.month_abbr[m])

            if selected_user == 'all':
                filtered_data = (data[(data['custom_category'] == selected_cat) & (data['date'].dt.year == selected_year)].
                                 groupby(by=['month_name']).agg({'amount': 'sum'}).reset_index())
                for m in range(12):
                    month_label = calendar.month_abbr[m+1]
                    if month_label not in filtered_data['month_name']:
                        filtered_data.loc[len(filtered_data.index)] = [month_label, 0]
                ordered_mths = [calendar.month_abbr[i + 1] for i in range(12)]
                filtered_data.index = pd.CategoricalIndex(filtered_data['month_name'], categories=ordered_mths, ordered=True)
                filtered_data = filtered_data.sort_index().reset_index(drop=True)
                bar_cat_by_month = px.bar(filtered_data, x='month_name', y='amount')
            else:
                filtered_data = (data[(data['custom_category'] == selected_cat) & (data['date'].dt.year == selected_year)].
                                 groupby(by=['user', 'month_name']).agg({'amount': 'sum'}).reset_index())
                filtered_data = filtered_data[filtered_data['user'] == selected_user]
                for u in data['user'].unique():
                    for x in range(12):
                        month_label = calendar.month_abbr[x+1]
                        if month_label not in filtered_data['month_name']:
                            filtered_data.loc[len(filtered_data.index)] = [u, month_label, 0]
                ordered_mths = [calendar.month_abbr[i + 1] for i in range(12)]
                filtered_data.index = pd.CategoricalIndex(filtered_data['month_name'], categories=ordered_mths, ordered=True)
                filtered_data = filtered_data.sort_index().reset_index(drop=True)
                bar_cat_by_month = px.bar(filtered_data, x='month_name', y='amount', color='user')

            filtered_data = filtered_data.loc[~(filtered_data == 0).any(axis=1)]
            agg_data = filtered_data['amount'].describe().reset_index()
            cols = [{'name': col, 'id': col} for col in agg_data.columns]
            table = agg_data.to_dict(orient='records')

            return table, cols, bar_cat_by_month, annual_breakdown_sankey

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
            data = self.data

            filtered_data = data[(data['date'].dt.month == self.months_dict[selected_month]) &
                                 (data['date'].dt.year == selected_year) &
                                 (data['custom_category'] != 'Payment')]

            # Pie Chart
            agg_data = filtered_data.groupby(['custom_category']).agg({'amount': 'sum'})
            pie_monthly_cat = px.pie(agg_data.reset_index(), values='amount', names='custom_category')

            # Bar Chart
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
