import calendar
import requests, json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go


def query_transactions(curs, username):
    curs.execute("SELECT * FROM transactions WHERE user_id LIKE (?)", (username,))
    data = curs.fetchall()
    # Data is returned as a dictionary
    return data


def query_user_income(curs, username):
    curs.execute("SELECT annual_income,side_income FROM users WHERE username LIKE (?)", (username,))
    data = curs.fetchall()
    return data


def query_trans_columns(curs):
    curs.execute("PRAGMA table_info(transactions)")
    data = curs.fetchall()
    # Data is returned as a dictionary
    return data


def query_user_columns(curs):
    curs.execute("PRAGMA table_info(users)")
    data = curs.fetchall()
    # Data is returned as a dictionary
    return data


def gen_dataframe(curs, username):
    df = pd.DataFrame.from_dict(query_transactions(curs, username))
    # Salaries
    df_income = pd.DataFrame.from_dict(query_user_income(curs, username))
    if len(df) == 0:
        df = pd.DataFrame.from_dict(query_trans_columns(curs))
        df = pd.DataFrame(columns=list(df['name']))
        df_income = pd.DataFrame.from_dict(query_user_columns(curs))
        overall_pie_user = px.pie(df, values='amount', names='user')
        overall_pie_cat = px.pie(df, values='amount', names='custom_category')
        return df, df_income, overall_pie_user, overall_pie_cat
    else:
        df['date'] = df['transaction_date'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
        df['amount'] = df['amount'].apply(lambda x: -x)
        df['category'] = df['category'].apply(lambda x: 'Shopping' if x == 'Normal' else x)
        df['user'] = df['user'].apply(lambda x: str(x).strip())

        # MORE DATA CLEANUP HERE

        # List of Countries and Cities to Bundle Travel Into
        url = 'https://raw.githubusercontent.com/russ666/all-countries-and-cities-json/master/countries.json'
        resp = requests.get(url)
        location_data = json.loads(resp.text)
        df['group'] = df['custom_category'].apply(lambda x: x if x in location_data else '')
        df['custom_category'] = (df['custom_category'].
                                 apply(lambda x: 'Travel' if x in location_data else x))

        # Categorical Text Filtering
        df['custom_category'] = (df['custom_category'].
                                 apply(lambda x: 'Health' if x in ['Necessities', 'Necessity'] else x))
        df['custom_category'] = (df['custom_category'].
                                 apply(lambda x: 'Food' if x in ['dining', 'Dining'] else x))
        df['custom_category'] = (df['custom_category'].
                                 apply(lambda x: 'Travel' if x in ['Travel Credit'] else x))

        df = df.drop_duplicates(subset=list(df.columns[df.columns != 'id']))

        overall_data = df[~df['custom_category'].isin(['Payment', 'Travel Credit'])]

        overall_data_user = overall_data.groupby(['user']).agg({'amount': 'sum'}).reset_index()
        overall_pie_user = px.pie(overall_data_user, values='amount', names='user')
        overall_pie_user.update_traces(text=overall_data_user['amount'].map("${:,}".format))

        overall_data_cat = overall_data.groupby(['custom_category']).agg({'amount': 'sum'}).reset_index()
        overall_data_cat.loc[len(overall_data_cat.index)] = \
            ['Other', overall_data_cat[overall_data_cat['amount'] < 500]['amount'].sum()]
        overall_data_cat = overall_data_cat[~(overall_data_cat['amount'] < 500)]
        overall_pie_cat = px.pie(overall_data_cat, values='amount', names='custom_category')

        return df, df_income, overall_pie_user, overall_pie_cat


def preprocess_df_for_db(df, user_id):
    trans_table_cols = ['user_id', 'transaction_date', 'post_date', 'description',
                        'category', 'amount', 'custom_category', 'user', 'custom_group', 'date']
    desired_dtypes = ['string', 'datetime64[ns]', 'datetime64[ns]', 'string', 'category',
                      'float64', 'category', 'string', 'string', 'datetime64[ns]']

    if len(df.columns) != len(trans_table_cols) - 2:
        raise IndexError("Number of columns is not the proper amount.")

    # add a user column
    df['user_id'] = user_id
    df.insert(0, 'user_id', df.pop('user_id'))
    print(df.head())

    df['date'] = df['Transaction Date'].apply(lambda x: datetime.strptime(x, '%m/%d/%y'))
    df = df.rename(mapper=dict(zip(df.columns, trans_table_cols)), axis=1)

    # Check data types
    for i, c in enumerate(df.columns):
        if df[c].dtype != desired_dtypes[i]:
            df[c] = df[c].astype(desired_dtypes[i])

    return df


def plot_sankey(df, df_income, year):
    df = df[(df['date'].dt.year == year) & (df['custom_category'] != 'Payment')]

    node_labels_start = ['Salary', 'Business']
    node_labels_start_weights = [df_income['annual_income'][0], df_income['side_income'][0]]
    node_labels_l1 = ['Total Income']
    node_labels_l2 = list(df['user'].unique())
    node_labels_l3 = list(df['custom_category'].unique())
    node_labels = node_labels_start + node_labels_l1 + node_labels_l2 + node_labels_l3
    node_df = pd.DataFrame(list(zip(list(range(len(node_labels))), node_labels)), columns=['ID', 'Label'])

    links_df2 = df.groupby(['user', 'custom_category']).agg({'amount': 'sum'}).reset_index()
    links_df2 = links_df2.rename(columns={'user': 'Source', 'custom_category': 'Target', 'amount': 'Weight'})

    # Total Money
    links_df1 = pd.DataFrame(columns=list(links_df2.columns))
    for name in node_labels_l2:
        links_df1.loc[len(links_df1.index)] = ['Total Income', name,
                                               links_df2[links_df2['Source'] == name]['Weight'].sum()]

    links_df0 = pd.DataFrame(columns=list(links_df2.columns))
    for i, item in enumerate(node_labels_start):
        links_df0.loc[len(links_df0.index)] = [item, 'Total Income', node_labels_start_weights[i]]

    links_df = pd.concat([links_df0, links_df1, links_df2])
    links_df = links_df.dropna().reset_index(drop=True)
    links_df = links_df[~links_df['Source'].str.contains("nan")]
    links_df = links_df[~links_df['Target'].str.contains("nan")]
    links_df['Weight'] = links_df['Weight'].apply(lambda x: abs(x))

    # Convert Sources and Targets to numbers
    links_df['Source'] = links_df['Source'].apply(
        lambda x: int(node_df.loc[node_df['Label'] == x]['ID'].reset_index(drop=True).iloc[0])
    )
    links_df['Target'] = links_df['Target'].apply(
        lambda x: int(node_df.loc[node_df['Label'] == x]['ID'].reset_index(drop=True).iloc[0])
    )

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_df['Label'].dropna(axis=0, how='any'),
            color="blue"
        ),
        link=dict(
            source=links_df['Source'].dropna(axis=0, how='any'),
            target=links_df['Target'].dropna(axis=0, how='any'),
            value=links_df['Weight'].dropna(axis=0, how='any')
        ))])

    fig.update_layout(title_text="Sankey Diagram", font_size=10)
    return fig
