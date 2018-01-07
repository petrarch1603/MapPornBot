from functions import *
import datetime
import time

# Post the top /r/MapPorn submission from the last week.
print('Begin Script to run top post of the week')
print(datetime.datetime.now())

loglist = []
loglist.append(datetime.datetime.now())
top = r.subreddit('mapporn').top('week', limit=1)
top = list(top)
top_week = (top[0])
announce_week = 'Top post of the week:\n'
logdict = {'type': 'socmediapost'}

try:
    output = shotgun_blast(raw_id_input=top_week, announce_input=announce_week)
    logdict['time'] = time.time()
    logobject = {'script': 'Top Post of Week'}
    logobject['message'] = str(output.message)
    logobject['tweet_url'] = str(output.tweet_url)
    logobject['tumblr_url'] = str(output.tumblr_url)
    logobject['fb_url'] = str(output.facebook_url)
    logdict['object'] = logobject
    addToJSON(logdict)

except Exception as ex:
    logdict['time'] = time.time()
    logdict['error'] = str(ex)
    addToJSON(logdict)
