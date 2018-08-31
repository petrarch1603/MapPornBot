import calendar
from classes import *
import datetime
from functions import shotgun_blast, send_reddit_message_to_self
import os
import praw
import random


print("Running This Day in History script")


def init():
    global hist_db, log_db, my_diag, r, today_int
    hist_db = HistoryDB()
    log_db = LoggingDB()
    my_diag = Diagnostic(script=os.path.basename(__file__))
    my_diag.table = 'historymaps'
    r = praw.Reddit('bot1')
    today_int = datetime.datetime.now().timetuple().tm_yday
    if today_int > 60 and calendar.isleap(datetime.datetime.now().year):
        today_int -= 1


init()
today_list = hist_db.get_rows_by_date(today_int)

if len(today_list) == 0:
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
    log_db.close()
    exit()

# Check if there are multiple entries with today's date
random_int = 0
if len(today_list) > 1:
    random_int = random.randint(0, (len(today_list) - 1))

raw_id = today_list[random_int][0][-6:]
my_diag.raw_id = raw_id
redditobject = r.submission(id=raw_id)
my_title = today_list[random_int][1]

try:
    x = shotgun_blast(raw_id_input=redditobject, title=my_title)
    my_diag.tweet = x.tweet_url
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
except Exception as shotgun_error:
    my_message = ('Error encountered: \n' + str(shotgun_error))
    my_diag.severity = 2
    my_diag.traceback = shotgun_error
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=my_message)
    send_reddit_message_to_self(title="Problem posting this day in history", message=my_message)
