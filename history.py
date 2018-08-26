import calendar
import datetime
import praw
import random
import sqlite3
from functions import shotgun_blast, send_reddit_message_to_self

# Connect to database
conn = sqlite3.connect('data/dayinhistory.db')
curs = conn.cursor()

# Connect to PRAW
r = praw.Reddit('bot1')

# Get today's date as day of year (1-366)
today_int = datetime.datetime.now().timetuple().tm_yday
if today_int > 60 and calendar.isleap(datetime.datetime.now().year):
    today_int -= 1

# Get all entries with today's date
today_list = []
for row in curs.execute("SELECT * FROM historymaps"):
    if (row[2]) == today_int:
        today_list.append(row)

if len(today_list) == 0:
    exit()

# Check if there are multiple entries with today's date
random_int = 0
if len(today_list) > 1:
    random_int = random.randint(0, (len(today_list) - 1))

raw_id = today_list[random_int][0][-6:]
redditobject = r.submission(id=raw_id)
my_title = today_list[random_int][1]

print(redditobject)
print(my_title)

try:
    x = shotgun_blast(raw_id_input=redditobject, title=my_title)
    my_message = ("Posted to Twitter: " + str(x.tweet_url))
except Exception as shotgun_error:
    my_message = ('Error encountered: \n' + str(shotgun_error))

send_reddit_message_to_self(title="This day in history script", message=my_message)

# TODO
# Add logging to a database

