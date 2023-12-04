import sqlite3
from gen_database import dict_factory


conn = sqlite3.connect('main.db', check_same_thread=False)
conn.row_factory = dict_factory
db = conn.cursor()

# db.execute(
#     "INSERT INTO users (username, hash) VALUES(?, ?)",
#     ("random_user_3", "lalala")
# )

db.execute("SELECT * FROM transactions LIMIT 5")
rows = db.fetchall()

for row in rows:
    print(row)

# conn.commit()
# conn.close()
