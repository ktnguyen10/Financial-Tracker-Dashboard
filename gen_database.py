import sqlite3
import pandas as pd


def init_database():
    conn = sqlite3.connect('main.db', check_same_thread=False)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute(
        "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
        "user_id TEXT NOT NULL, transaction_date TEXT NOT NULL, post_date TEXT NOT NULL, "
        "description TEXT NOT NULL, category TEXT, amount NUMERIC NOT NULL, custom_category TEXT, "
        "user TEXT) "
        )
    curs.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
        "username TEXT NOT NULL, hash TEXT NOT NULL) "
    )
    conn.commit()
    return conn, curs


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def read_file_to_db(conn, curs, file, user_id):
    trans_table_cols = ['user_id', 'transaction_date', 'post_date', 'description',
                        'category', 'amount', 'custom_category', 'user']

    print("Uploading " + str(file))
    df = pd.read_csv(file, encoding='unicode_escape')
    print(df.head())

    # add a user column
    df['user_id'] = user_id
    df.insert(0, 'user_id', df.pop('user_id'))
    print(df.head())

    df = df.rename(mapper=dict(zip(df.columns, trans_table_cols)), axis=1)

    df.to_sql('transactions', conn, if_exists='append', index=False)  # write df into the database
    # curs.execute("""
    #     UPDATE transactions
    #     SET ID = temp.column_list
    #     FROM temporary_table AS temp
    #     WHERE transactions.id = temp.id;
    #     """)  # update the schedule table in the database
    # curs.execute('DROP TABLE temporary_table')
    # conn.commit()
