import datetime
from functions import shotgun_blast, send_reddit_message_to_self
import praw
import random
import sqlite3
import time


# This script will only be scoped to post from the socmedia database to social media.
# Checking the inbox and storing to the database will be done in checkinbox.py
print("Running social media stack script.")

# Connect to database and PRAW
conn = sqlite3.connect('data/socmedia.db')
curs = conn.cursor()
r = praw.Reddit('bot1')

# Deal with time zone and hour
popular_hour = 9


def get_target_hour(popular_hour_arg):
    utc_now = datetime.datetime.utcnow().hour
    target = popular_hour_arg - utc_now
    if target < -11:
        target += 24
    elif target > 12:
        target -= 24
    return target


def get_map(target_hour):  # Get a map that is in the target_hour hour range
    mintarget = (int(target_hour) - 3)
    maxtarget = (int(target_hour) + 3)
    if mintarget < -11:
        mintarget += 24
    elif maxtarget > 12:
        maxtarget -= 24
    targetmaplist = []
    for row in curs.execute(
        "SELECT * FROM socmediamaps WHERE fresh=1 AND time_zone >= {mintarget} AND time_zone <= {maxtarget}"
            .format(mintarget=mintarget, maxtarget=maxtarget)):
        targetmaplist.append(row)
    if len(targetmaplist) == 0:
        for row in curs.execute("SELECT * FROM socmediamaps WHERE fresh=1 AND time_zone = 99"):
            targetmaplist.append(row)
    if len(targetmaplist) == 0:  # If it's still zero
        # TODO: choose the time zone that is most frequently in the database, not a random map.
        my_map = curs.execute("SELECT * FROM socmediamaps WHERE fresh=1 ORDER BY RANDOM() LIMIT 1").fetchone()
    else:
        random_int = random.randint(0, (len(targetmaplist) - 1))
        my_map = targetmaplist[random_int]
    try:
        print("Title: " + str(my_map[1]))
    except Exception:
        print('Could not print my_map[1]')
    return my_map


def not_fresh(my_map_arg):
    old_count = list(curs.execute(
        "SELECT count(*) FROM socmediamaps WHERE fresh = 0"
    ))[0][0]

    curs.execute('''UPDATE socmediamaps SET fresh=0 WHERE raw_id=?''', (my_map_arg[0],))
    curs.execute('''UPDATE socmediamaps SET date_posted=? WHERE raw_id=?''', (int(time.time()), my_map_arg[0],))
    new_count = list(curs.execute(
        "SELECT count(*) FROM socmediamaps WHERE fresh = 0"
    ))[0][0]

    try:
        assert new_count == (old_count + 1)
    except Exception as e:
        # TODO: Add Logging
        error_message = ('Error: new fresh count is different than old fresh count.' + str(e))
        send_reddit_message_to_self(title="Fresh count wrong", message=error_message)


def postsocmedia(my_map_arg):
    error_message = ''
    redditobject = r.submission(id=my_map_arg[0])
    try:
        blast = shotgun_blast(raw_id_input=redditobject, title=my_map_arg[1])
        not_fresh(my_map_arg)
        print(blast.tweet_url)
        # TODO: Add logging
    except Exception as e:
        error_message = ("Error Encountered: \n"
                         "Could not post to social media.\n" + str(e))
        send_reddit_message_to_self(title="Error with Social Media Post", message=error_message)
    return error_message


my_map_global = get_map(get_target_hour(popular_hour))
status = postsocmedia(my_map_global)
if status == '':
    # TODO log success
    conn.commit()
    conn.close()
    print('Successfully posted to social media')
