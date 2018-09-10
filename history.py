import calendar
from classes import *
import datetime
from functions import send_reddit_message_to_self
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
praw_obj = r.submission(id=raw_id)
my_title = today_list[random_int][1]
my_diag.title = my_title

try:
    s_b = ShotgunBlast(praw_obj, title=my_title)
    assert s_b.check_integrity() == "PASS"
    s_b_dict = s_b.post_to_all_social()
    my_diag.tweet = s_b_dict['tweet_url']
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
except Exception as shotgun_error:
    errorMessage = ('Error encountered: \n' + str(shotgun_error))
    my_diag.severity = 2
    my_diag.traceback = errorMessage
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=errorMessage)
    send_reddit_message_to_self(title="Problem posting this day in history", message=errorMessage)
