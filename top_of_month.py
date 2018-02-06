from functions import *
import time

# Post the top /r/MapPorn submission from the last month.


top = r.subreddit('mapporn').top('month', limit=1)
top = list(top)
top_month = (top[0])
announce_month = 'Top post of the month:\n'
logdict = {'type': 'socmediapost'}

try:
    social_media_post = shotgun_blast(raw_id_input=top_month, announce_input=announce_month)
    logdict['time'] = time.time()
    logobject = {'script': 'Top Post of Month',
                 'message': str(social_media_post.message),
                 'tweet_url': str(social_media_post.tweet_url),
                 'tumblr_url': str(social_media_post.tumblr_url),
                 'fb_url': str(social_media_post.facebook_url)}
    logdict['object'] = logobject
    addToMongo(logdict)
except Exception as ex:
    logdict['time'] = time.time()
    logdict['error'] = str(ex)
    addToMongo(logdict)
