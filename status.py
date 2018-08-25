from functions import SQLiteFunctions
import sqlite3

conn = sqlite3.connect('dayinhistory.db')
curs = conn.cursor()

historyDBstatus = SQLiteFunctions.check_historyDB_integrity()
historyDB_rows = SQLiteFunctions.total_rows(cursor=curs, table_name='historymaps')
print(historyDB_rows)
print(historyDBstatus)