from functions import SQLiteFunctions
import sqlite3

conn = sqlite3.connect('data/dayinhistory.db')
curs = conn.cursor()

historyDBstatus = SQLiteFunctions.check_historyDB_integrity()
historyDB_rows = SQLiteFunctions.total_rows(cursor=curs, table_name='historymaps')
socmediaDBstatus = SQLiteFunctions.check_socmediaDB_integrity()

print(historyDB_rows)
print(historyDBstatus)
print(socmediaDBstatus)

refreshed = SQLiteFunctions.make_fresh_again()
print(refreshed)