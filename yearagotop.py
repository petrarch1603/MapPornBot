from time import mktime
from functions import *
import datetime

yearago = datetime.datetime.now() - datetime.timedelta(days=1*365)
lessthanyearago = datetime.datetime.now() - datetime.timedelta(days=1*360)
highesttimestamp = int(mktime(yearago.timetuple()))
lowesttimestamp = int(mktime(lessthanyearago.timetuple()))

loglist = []
loglist.append(datetime.datetime.now())

subreddit = r.subreddit('mapporn')
for submission in subreddit.submissions(highesttimestamp, lowesttimestamp):
    raw_id = submission
    break

try:
    post = shotgun_blast(raw_id_input=raw_id, announce_input='')
    loglist.append(post)
except:
    loglist.append('Unable to post yearagotop to social media')

with open('logs/prettylog.txt', 'a') as logfile:
    for i in loglist:
        logfile.write(str(i))
    logfile.write('-------------')
