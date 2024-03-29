import sqlite3
import pandas as pd
from datetime import datetime
from financial_dashboard.dashboard.data_cleanup import preprocess_df_for_db


def init_database():
    conn = sqlite3.connect('../main.db', check_same_thread=False)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute(
        "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
        "user_id TEXT NOT NULL, transaction_date TEXT NOT NULL, post_date TEXT NOT NULL, "
        "description TEXT NOT NULL, category TEXT, amount NUMERIC NOT NULL, custom_category TEXT, "
        "user TEXT, custom_group TEXT, date TEXT NOT NULL) "
    )
    curs.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
        "username TEXT NOT NULL, hash TEXT NOT NULL, annual_income NUMERIC NOT NULL, side_income NUMERIC NOT NULL) "
    )
    conn.commit()
    return conn, curs


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def read_file_to_db(conn, curs, file, user_id):
    print("Uploading " + str(file))
    df = pd.read_csv(file, encoding='unicode_escape')
    print(df.head())

    df = preprocess_df_for_db(df, user_id)

    # write df into the database
    df.to_sql('transactions', conn, if_exists='append', index=False)
