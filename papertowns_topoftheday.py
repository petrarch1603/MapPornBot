from functions import *
import datetime

# Post the top /r/MapPorn submission from the last week.


loglist = []
loglist.append(datetime.datetime.now())

try:
    (subreddit, subtitle, social_media_post) = subreddit_top_post(subreddit='papertowns', time_window='day')
    loglist.append(social_media_post)
except:
    loglist.append('Unable to submit papertowns_topoftheday to social media.')

with open('logs/prettylog.txt', 'a') as logfile:
    for i in loglist:
        logfile.write(str(i))
    logfile.write('-------------')



