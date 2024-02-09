from financial_dashboard.database import Database

db = Database()
conn, curs = db.new_database()
__all__ = ['paths']
