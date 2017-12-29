from functions import *


loglist = []
loglist.append(datetime.datetime.now())
try:
    (subreddit, subtitle, social_media_post) = subreddit_top_post(subreddit='oldmaps', time_window='week')
    loglist.append(social_media_post)
except:
    loglist.append('Unable to submit oldmaps_topoftheday to social media')


with open('logs/prettylog.txt', 'a') as logfile:
    for i in loglist:
        logfile.write(str(i))
    logfile.write('-------------')
