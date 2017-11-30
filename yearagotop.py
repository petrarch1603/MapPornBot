from time import mktime
from functions import *
import datetime

yearago = datetime.datetime.now() - datetime.timedelta(days=1*365)
lessthanyearago = datetime.datetime.now() - datetime.timedelta(days=1*360)
highesttimestamp = int(mktime(yearago.timetuple()))
lowesttimestamp = int(mktime(lessthanyearago.timetuple()))


subreddit = r.subreddit('mapporn')
for submission in subreddit.submissions(highesttimestamp, lowesttimestamp):
    raw_id = submission
    break

post = shotgun_blast(raw_id_input=raw_id, announce_input='')
print(post)
