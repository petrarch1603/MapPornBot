import datetime
from classes import *
from functions import shotgun_blast, send_reddit_message_to_self
import os
import praw


# This script will only be scoped to post from the socmedia database to social media.
# Checking the inbox and storing to the database will be done in checkinbox.py
print("Running social media stack script.")


def init():
    global soc_db, log_db, r, my_diag, popular_hour
    soc_db = SocMediaDB()
    log_db = LoggingDB()
    my_diag = Diagnostic(script=os.path.basename(__file__), database="SocMediaDB")
    r = praw.Reddit('bot1')
    popular_hour = 9


def get_target_hour(popular_hour_arg):
    utc_now = datetime.datetime.utcnow().hour
    target = popular_hour_arg - utc_now
    if target < -11:
        target += 24
    elif target > 12:
        target -= 24
    return target


def postsocmedia(map_row):
    error_message = ''
    redditobject = r.submission(id=map_row.dict['raw_id'])
    try:
        blast = shotgun_blast(raw_id_input=redditobject, title=map_row.dict['text'])
        soc_db.update_to_not_fresh(raw_id=map_row.dict['raw_id'])
        print(blast.tweet_url)
        # TODO: Add logging
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
    except Exception as e:
        error_message = ("Error Encountered: \n"
                         "Could not post to social media.\n" + str(e) + "\nMap with problem: \n" + map_row['text'])
        send_reddit_message_to_self(title="Error with Social Media Post", message=error_message)
        my_diag.traceback = error_message
        my_diag.severity = 1
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
    return error_message


status = postsocmedia(soc_db.get_one_map_row(target_zone=popular_hour))
if status == '':
    # TODO log success
    soc_db.conn.commit()
    soc_db.close()
    print('Successfully posted to social media')
