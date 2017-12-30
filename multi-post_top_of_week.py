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
try:
    output = shotgun_blast(raw_id_input=top_week, announce_input=announce_week)
    d = {'type': 'socmediapost'}
    d['script'] = 'Top Post of Week'
    d['message'] = output.message
    d['tweet_url'] = output.tweet_url
    d['tumblr_url'] = output.tumblr_url
    d['fb_url'] = output.facebook_url
    loglist.append(d)
except Exception as ex:
    loglist.append(ex)


with open('logs/prettylog.txt', 'a') as logfile:
    for i in loglist:
        logfile.write(str(i))
    logfile.write('-------------')

