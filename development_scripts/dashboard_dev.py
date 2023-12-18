import pandas as pd
import calendar
import os
import glob
from io import StringIO
from datetime import datetime, date
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import dash_table
import plotly.express as px

months_dict = {month: index for index, month in enumerate(calendar.month_name) if month}
years_list = [i for i in range(2022, 2024)]

# Data preparation
os.chdir(os.getcwd())
result = glob.glob('*.{}'.format('csv'))

data = pd.DataFrame()
for file in result:
    temp = pd.read_csv(file)
    data = pd.concat([data, temp])
# data = pd.read_csv('Finances for Kevin and Mon - Sapphire Preferred.csv')
data['Date'] = data['Transaction Date'].apply(lambda x: datetime.strptime(x, '%m/%d/%y'))
data['Amount'] = data['Amount'].apply(lambda x: -x)
data['Custom Category'] = data['Custom Category'].apply(lambda x: 'Shopping' if x == 'Normal' else x)

# Prepare Overall Data
overall_data = data[~data['Custom Category'].isin(['Payment', 'Travel Credit'])]

overall_data_user = overall_data.groupby(['User']).agg({'Amount': 'sum'}).reset_index()
overall_pie_user = px.pie(overall_data_user, values='Amount', names='User')
overall_pie_user.update_traces(text=overall_data_user['Amount'].map("${:,}".format))

overall_data_cat = overall_data.groupby(['Custom Category']).agg({'Amount': 'sum'}).reset_index()
other_cols = overall_data_cat[overall_data_cat['Amount'] < 500].dropna(axis=1).columns
overall_data_cat.loc[len(overall_data_cat.index)] = \
    ['Other', overall_data_cat[overall_data_cat['Amount'] < 500]['Amount'].sum()]
overall_data_cat = overall_data_cat[~(overall_data_cat['Amount'] < 500)]
overall_pie_cat = px.pie(overall_data_cat, values='Amount', names='Custom Category')
# overall_pie_cat.update_traces(text=overall_data_cat['Amount'].map("${:,}".format))

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
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

    # dbc.Row([
    #     dbc.Col([
    #         dag.AgGrid(
    #             id='monthly-finance-table',
    #             rowData=pd.DataFrame.to_dict("records"),
    #             dashGridOptions={"rowSelection": "single"},
    #             columnDefs=[{"field": i, "filter": "agSetColumnFilter"} for i in months_list],
    #             columnSize="sizeToFit",
    #             columnSizeOptions={
    #                 'defaultMinWidth': 250,
    #             },
    #         ),
    #     ]),
    # ], className='mt-4'),

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


@app.callback(
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


@app.callback(
    [Output('top-spend-table', 'data'),
     Output('top-spend-table', 'columns')],
    Input('table_memory', 'data')
)
def update_monthly_cat_spend(clean_data):
    agg_data = pd.read_json(StringIO(clean_data))
    cols = [{'name': col, 'id': col} for col in agg_data.columns]
    table = agg_data.to_dict(orient='records')
    return table, cols


if __name__ == '__main__':
    app.run_server(debug=True, port=8002)
