from functions import *
import datetime
import time

# Post the top /r/MapPorn submission from the last week.

top = r.subreddit('mapporn').top('week', limit=1)
top = list(top)
top_week = (top[0])
announce_week = 'Top post of the week:\n'
logdict = {'type': 'socmediapost'}

try:
    social_media_post = shotgun_blast(raw_id_input=top_week, announce_input=announce_week)
    logdict['time'] = time.time()
    logobject = {'script': 'Top Post of Week'}
    logobject['message'] = str(social_media_post.message)
    logobject['tweet_url'] = str(social_media_post.tweet_url)
    logobject['tumblr_url'] = str(social_media_post.tumblr_url)
    logobject['fb_url'] = str(social_media_post.facebook_url)
    logdict['object'] = logobject
    addToMongo(logdict)

except Exception as ex:
    logdict['time'] = time.time()
    logdict['error'] = str(ex)
    addToMongo(logdict)
