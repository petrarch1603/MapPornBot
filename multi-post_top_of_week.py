from functions import *
import datetime

# Post the top /r/MapPorn submission from the last week.
print('Begin Script to run top post of the week')
print(datetime.datetime.now())


top = r.subreddit('mapporn').top('week', limit=1)
top = list(top)
top_week = (top[0])
announce_week = 'Top post of the week:\n'
shotgun_blast(raw_id_input=top_week, announce_input=announce_week)
print('End script to run top post of the last week')
