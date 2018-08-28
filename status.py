from functions import SQLiteFunctions
import sqlite3

history_conn = sqlite3.connect('data/dayinhistory.db')
history_curs = history_conn.cursor()

soc_conn = sqlite3.connect('data/socmedia.db')
soc_curs = soc_conn.cursor()

def time_zone_analysis():
    zone_dict = {}
    zone_dict['n_america'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (-9,-8,-7,-6,-5) AND fresh = 1").fetchone()[0]
    zone_dict['s_america'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (-5,-4,-3) AND fresh=1").fetchone()[0]
    zone_dict['w_europe'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (0,1) AND fresh=1").fetchone()[0]
    zone_dict['e_europe'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (2,3) AND fresh=1").fetchone()[0]
    zone_dict['c_asia'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (4,5,6) AND fresh=1").fetchone()[0]
    zone_dict['e_asia'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (7,8,9) AND fresh=1").fetchone()[0]
    zone_dict['oceania'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (10,11,12,-10) AND fresh=1").fetchone()[0]
    zone_dict['no_zone'] = soc_curs.execute("SELECT count(*) FROM socmediamaps WHERE time_zone in (99) AND fresh=1").fetchone()[0]
    for k, v in zone_dict.items():
        if v < 10:
            print(str(k) + " is low on maps, please add some more.")



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
time_zone_analysis()
history_conn.close()
soc_conn.close()
