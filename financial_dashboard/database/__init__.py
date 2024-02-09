import sqlite3
import pandas as pd
from datetime import datetime


class Database:
    def __init__(self):
        self.conn = None
        self.curs = None

    def new_database(self):
        self.conn = sqlite3.connect('main.db', check_same_thread=False)
        self.conn.row_factory = self.dict_factory
        self.curs = self.conn.cursor()
        self.curs.execute(
            "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
            "user_id TEXT NOT NULL, transaction_date TEXT NOT NULL, post_date TEXT NOT NULL, "
            "description TEXT NOT NULL, category TEXT, amount NUMERIC NOT NULL, custom_category TEXT, "
            "user TEXT, custom_group TEXT, date TEXT NOT NULL) "
        )
        self.curs.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
            "username TEXT NOT NULL, hash TEXT NOT NULL, annual_income NUMERIC NOT NULL, side_income NUMERIC NOT NULL) "
        )
        self.conn.commit()

        return self.conn, self.curs

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @staticmethod
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

    def read_file_to_db(self, file, user_id):
        print("Uploading " + str(file))
        df = pd.read_csv(file, encoding='unicode_escape')
        print(df.head())

        df = self.preprocess_df_for_db(df, user_id)

        # write df into the database
        df.to_sql('transactions', self.conn, if_exists='append', index=False)
