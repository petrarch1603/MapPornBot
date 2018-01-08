from time import mktime
from functions import *
import datetime
import time

yearago = datetime.datetime.now() - datetime.timedelta(days=1*365)
lessthanyearago = datetime.datetime.now() - datetime.timedelta(days=1*360)
highesttimestamp = int(mktime(yearago.timetuple()))
lowesttimestamp = int(mktime(lessthanyearago.timetuple()))

subreddit = r.subreddit('mapporn')
for submission in subreddit.submissions(highesttimestamp, lowesttimestamp):
    raw_id = submission
    break

logdict = {'type': 'socmediapost'}


try:
    social_media_post = shotgun_blast(raw_id_input=raw_id, announce_input='')
    logdict['time'] = time.time()
    logobject = {'script': 'Top Year Ago',
                 'message': str(social_media_post.message),
                 'tweet_url': str(social_media_post.tweet_url),
                 'tumblr_url': str(social_media_post.tumblr_url),
                 'fb_url': str(social_media_post.facebook_url)}
    logdict['object'] = logobject
    addToJSON(logdict)

except Exception as ex:
    logdict['time'] = time.time()
    logdict['post'] = 'yearagotop.py'
    logdict['error'] = str(ex)
    addToJSON(logdict)
