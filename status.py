from functions import SQLiteFunctions
import sqlite3

history_conn = sqlite3.connect('data/dayinhistory.db')
history_curs = history_conn.cursor()

soc_conn = sqlite3.connect('data/socmedia.db')
soc_curs = soc_conn.cursor()

historyDBstatus = SQLiteFunctions.check_historyDB_integrity()
historyDB_rows = SQLiteFunctions.total_rows(cursor=history_curs, table_name='historymaps')
socmediaDBstatus = SQLiteFunctions.check_socmediaDB_integrity()
socmediaDB_rows = SQLiteFunctions.total_rows(cursor=soc_curs, table_name='socmediamaps')
print(historyDBstatus)
print("History Rows: " + str(historyDB_rows))
print(socmediaDBstatus)
print("Social Media Rows: " + str(socmediaDB_rows))

refreshed = SQLiteFunctions.make_fresh_again()
print(refreshed)

history_conn.close()
soc_conn.close()
