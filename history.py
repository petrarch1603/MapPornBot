import calendar
import csv
import datetime
import praw
import random

from functions import shotgun_blast, send_reddit_message_to_self

r = praw.Reddit('bot1')

today_int = datetime.datetime.now().timetuple().tm_yday

if today_int > 60 and calendar.isleap(datetime.datetime.now().year):
    today_int -= 1


with open('data/historicdates.csv', 'r') as f:
    reader = csv.reader(f)
    my_list = list(reader)

today_list = []
for line in my_list:
    if int(line[0]) == today_int:
        today_list.append(line)

if len(today_list) == 0:
    exit()

random_int = 0
if len(today_list) > 1:
    random_int = random.randint(1, len(today_list))

raw_id = today_list[random_int][2][-6:]
redditobject = r.submission(id=raw_id)
my_title = today_list[random_int][1]


try:
    x = shotgun_blast(raw_id_input=redditobject, title=my_title)
    my_message = ("Posted to Twitter: " + str(x.tweet_url))
except Exception as shotgun_error:
    my_message = ('Error encountered: \n' + str(shotgun_error))

send_reddit_message_to_self(title="This day in history script", message=my_message)
