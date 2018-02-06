from functions import *
import time

logdict = {'type': 'socmediapost'}

try:
    (subreddit, subtitle, social_media_post) = subreddit_top_post(subreddit='papertowns', time_window='day')
    logdict['time'] = time.time()
    logobject = {'script': 'Papertowns Top Post of Week', 'message': str(social_media_post.message),
                 'tweet_url': str(social_media_post.tweet_url), 'tumblr_url': str(social_media_post.tumblr_url),
                 'fb_url': str(social_media_post.facebook_url)}
    logdict['object'] = logobject
    addToMongo(logdict)

except Exception as ex:
    logdict['time'] = time.time()
    logdict['error'] = str(ex)
    addToMongo(logdict)
