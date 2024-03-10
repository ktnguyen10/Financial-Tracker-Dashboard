import dash_bootstrap_components as dbc
import plotly.express as px
from login_manager import LoginManager
import pandas as pd
import calendar, itertools
from financial_dashboard.dashboard.data_cleanup import gen_dataframe, plot_sankey
from dash import Dash, html, dcc, Input, Output, State, dash_table
from helpers import login_required
from datetime import datetime
from io import StringIO


class DashBoard:
    def __init__(self, flask_app, curs):
        self.data = pd.DataFrame
        self.income_data = pd.DataFrame
        self.items = []
        self.users = []
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
        user_list.append('All')
        self.users = user_list

        items = sorted(list(data['description'].unique()))
        items = [list(g) for _, g in itertools.groupby(items, lambda x: x.partition(' ')[0])]
        item_list = []
        for i in items:
            if len(i) == 1:
                item_list.append(i[0])
            elif any(common in i[0][0:3] for common in ['SJ ', 'SQ ', 'SP ']):
                for j in i:
                    item_list.append(j)
            else:
                item_list.append(i[0].partition(' ')[0])

        self.items = item_list

        layout = html.Div([
            dcc.Location(id='url', refresh=True),

            dcc.Store(id='table_memory'),

            html.H1(username + " Financial Dashboard", style={'textAlign': 'center'}),

            html.A(html.Button("Go Home", id="go_home", n_clicks='0'), href='/'),
            html.A(html.Button("Refresh", id="refresh_data", n_clicks='0'), href='/dashboard'),

            #### SECTION 1: By Month ####
            html.H2("Annual Spending by Category", style={'textAlign': 'center'}),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='cat_choice',
                        value=(list(data['custom_category'].unique())[0] if list(data['custom_category'].unique()) else ''),
                        clearable=False,
                        options=list(data['custom_category'].unique()) + ['All'])
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

            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='month-by-category-heatmap', figure={})
                ], width=12, md=6),
                dbc.Col([
                    dcc.Graph(id='month-by-user-heatmap', figure={})
                ], width=12, md=6)
            ], align='center'),

            dbc.Row([
                dbc.Col([
                    dash_table.DataTable(id='category-statistics')
                ], width=3),
            ], align='center'),

            #### SECTION 2: Monthly Breakdown ####
            # Add Total Money Spent this Month

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

            #### SECTION 3: Item Search
            # Make each item searchable
            html.H2("Spending By Item", style={'textAlign': 'center'}),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='item_choice',
                        value=item_list[0],
                        clearable=False,
                        options=item_list)
                ], width=4),
                dbc.Col([
                    dcc.Dropdown(
                        id='year_choice_3',
                        value=datetime.now().year,
                        clearable=False,
                        options=list(self.years_list))
                ], width=4),
                dbc.Col([
                    dcc.Input(id="item_search", type="text", placeholder="", style={'marginRight': '10px'}),
                    html.Button("Search", id="search_button", n_clicks='0')
                ], width=4)
            ]),

            # Line Chart for Every Item (amount vs date)
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='item_by_month', figure={})
                ], width=12)
            ], className='mt-4'),

            #### SECTION 4: Overall ####
            html.H2("Overall Spending", style={'textAlign': 'center'}),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='overall-pie-user', figure=overall_pie_user)
                ], width=12, md=6),
                dbc.Col([
                    dcc.Graph(id='overall-pie-cat', figure=overall_pie_cat)
                ], width=12, md=6)
            ], className='mt-4'),

            #### SECTION 5: Tables ####
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
            [Output('annual-breakdown-sankey', 'figure'),
             Output('month-by-category-heatmap', 'figure'),
             Output('month-by-user-heatmap', 'figure')],
            Input('year_choice_1', 'value')
        )
        def annual_data(selected_year):
            data = self.data
            income = self.income_data
            data['month'] = data['date'].dt.month
            data['month_name'] = data['month'].apply(lambda m: calendar.month_abbr[m])

            # Sankey
            annual_breakdown_sankey = plot_sankey(data, income, selected_year)

            # Category Heatmaps

            # ENABLE SORTING
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

            agg_data = (data[(data['date'].dt.year == selected_year) & (data['custom_category'] != 'Payment')].
                        groupby(['month_name', 'custom_category']).agg(total=('amount', 'sum')).reset_index())
            agg_data['month_name'] = pd.Categorical(agg_data['month_name'], categories=months, ordered=True)
            agg_data = agg_data.sort_values(by=['custom_category', 'month_name'])
            cat_data = agg_data.pivot(index='custom_category', columns='month_name', values='total')
            cat_heatmap = px.imshow(cat_data, y=cat_data.index, x=cat_data.columns)

            agg_data = (data[(data['date'].dt.year == selected_year) & (data['custom_category'] != 'Payment')].
                        groupby(['month_name', 'user']).agg(total=('amount', 'sum')).reset_index())
            agg_data['month_name'] = pd.Categorical(agg_data['month_name'], categories=months, ordered=True)
            agg_data = agg_data.sort_values(by=['user', 'month_name'])
            user_data = agg_data.pivot(index='user', columns='month_name', values='total')
            user_heatmap = px.imshow(user_data, y=user_data.index, x=user_data.columns)

            return annual_breakdown_sankey, cat_heatmap, user_heatmap

        @dashapp.callback(
            Output('item_by_month', 'figure'),
            Input('search_button', 'n_clicks'),
            [State('item_search', 'value'),
             State('item_choice', 'value'),
             State('year_choice_3', 'value')],
            prevent_initial_call=True
        )
        def item_search(n, searched_item, selected_item, selected_year):
            data = self.data
            data['month'] = data['date'].dt.month
            data['month_name'] = data['month'].apply(lambda m: calendar.month_abbr[m])
            item_list = self.items

            if (searched_item != '') & (searched_item is not None):
                # Override chosen item if search bar is used
                # Find the closest matching string
                invalid_search_token = False

                filtered_data = data[(data['description'].str.lower().str.contains(searched_item.lower())) &
                                     (data['date'].dt.year == selected_year)].reset_index(drop=True)
                selected_item = filtered_data['description'][0]

                if filtered_data.shape[0] == 0:
                    invalid_search_token = True
                #     elif fuzz.token_set_ratio(searched_item, i) > 85:
                #         # For Mispellings, fuzzysearch
                #         selected_item = i
                #         break
            else:
                filtered_data = data[(data['description'] == selected_item) &
                                     (data['date'].dt.year == selected_year)].reset_index(drop=True)

                if filtered_data.shape[0] == 0:
                    filtered_data = data[(data['description'].str.lower().str.contains(selected_item.lower())) &
                                         (data['date'].dt.year == selected_year)].reset_index(drop=True)

            agg_data = filtered_data.groupby(['user', 'month_name']).agg(total=('amount', 'sum')).reset_index()
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            agg_data['month_name'] = pd.Categorical(agg_data['month_name'], categories=months, ordered=True)
            agg_data = agg_data.sort_values(by=['user', 'month_name'])
            item_by_month = px.line(agg_data, x='month_name', y='total',
                                    color='user', title=selected_item, markers=True)

            return item_by_month

        @dashapp.callback(
            [Output('category-statistics', 'data'),
             Output('category-statistics', 'columns'),
             Output('category-by-month-bar', 'figure')],
            [Input('cat_choice', 'value'),
             Input('year_choice_1', 'value'),
             Input('user_choice', 'value')]
        )
        def category_statistics(selected_cat, selected_year, selected_user):
            data = self.data
            data['month'] = data['date'].dt.month
            data['month_name'] = data['month'].apply(lambda m: calendar.month_abbr[m])

            if selected_user == 'All':
                if selected_cat == 'All':
                    filtered_data = (data[(data['custom_category'] != 'Payment') &
                                          (data['date'].dt.year == selected_year)].
                                     groupby(by=['month_name']).agg({'amount': 'sum'}).reset_index())
                else:
                    filtered_data = (data[(data['custom_category'] == selected_cat) &
                                          (data['date'].dt.year == selected_year)].
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
                if selected_cat == 'All':
                    filtered_data = (data[(data['custom_category'] != 'Payment') &
                                          (data['date'].dt.year == selected_year)].
                                     groupby(by=['user', 'month_name']).agg({'amount': 'sum'}).reset_index())
                else:
                    filtered_data = (data[(data['custom_category'] == selected_cat) &
                                          (data['date'].dt.year == selected_year)].
                                     groupby(by=['user', 'month_name']).agg({'amount': 'sum'}).reset_index())
                filtered_data = filtered_data[filtered_data['user'] == selected_user]
                for u in data['user'].unique():
                    for m in range(12):
                        month_label = calendar.month_abbr[m+1]
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
