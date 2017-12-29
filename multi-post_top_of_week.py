from functions import *
import datetime

# Post the top /r/MapPorn submission from the last week.
print('Begin Script to run top post of the week')
print(datetime.datetime.now())

loglist = []
loglist.append(datetime.datetime.now())
top = r.subreddit('mapporn').top('week', limit=1)
top = list(top)
top_week = (top[0])
announce_week = 'Top post of the week:\n'
output = shotgun_blast(raw_id_input=top_week, announce_input=announce_week)
loglist.append(output)
print('End script to run top post of the last week')

with open('logs/prettylog.txt', 'a') as logfile:
    for i in loglist:
        logfile.write(str(i))
    logfile.write('-------------')

