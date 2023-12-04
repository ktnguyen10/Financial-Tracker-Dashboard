import calendar
import pandas as pd
from datetime import datetime
import plotly.express as px


def query_transactions(curs, username):
    curs.execute("SELECT * FROM transactions WHERE user_id LIKE (?)", (username,))
    data = curs.fetchall()
    # Data is returned as a dictionary
    return data


def gen_dataframe(curs, username):
    df = pd.DataFrame.from_dict(query_transactions(curs, username))
    if len(df) == 0:
        return None
    df['date'] = df['transaction_date'].apply(lambda x: datetime.strptime(x, '%m/%d/%y'))
    df['amount'] = df['amount'].apply(lambda x: -x)
    df['category'] = df['category'].apply(lambda x: 'Shopping' if x == 'Normal' else x)

    overall_data = df[~df['custom_category'].isin(['Payment', 'Travel Credit'])]

    overall_data_user = overall_data.groupby(['user']).agg({'amount': 'sum'}).reset_index()
    overall_pie_user = px.pie(overall_data_user, values='amount', names='user')
    overall_pie_user.update_traces(text=overall_data_user['amount'].map("${:,}".format))

    overall_data_cat = overall_data.groupby(['custom_category']).agg({'amount': 'sum'}).reset_index()
    # other_cols = overall_data_cat[overall_data_cat['amount'] < 500].dropna(axis=1).columns
    overall_data_cat.loc[len(overall_data_cat.index)] = \
        ['Other', overall_data_cat[overall_data_cat['amount'] < 500]['amount'].sum()]
    overall_data_cat = overall_data_cat[~(overall_data_cat['amount'] < 500)]
    overall_pie_cat = px.pie(overall_data_cat, values='amount', names='custom_category')

    return df, overall_pie_user, overall_pie_cat

