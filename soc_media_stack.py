# This script spaces out the submissions to social media.
#
# This way I can add multiple social media posts simultaneously and they won't all post at once.
# Instead they will be added as objects to a stack. Every few hours the script will run and submit one social media post
# at a time.

import os
import pickle
import praw
import time
from functions import addToMongo, StackObject, shotgun_blast

r = praw.Reddit('bot1')
logdict = {}
newMessage = 'false'

with open('data/socmedia.pkl', 'rb') as f:
    mapstackold = (pickle.load(f))

urllist = mapstackold.urllist()

# When mapstack is empty it throws an error when trying to access urllist.
if not urllist:
    urllist = []



def postsocmedia(stack):
    newsocmediapost = stack.pop()
    if newsocmediapost != "Stack Empty!":
        raw_url = str(newsocmediapost.url[-6:])
        redditobject = r.submission(id=raw_url)
        x = shotgun_blast(raw_id_input=redditobject, title=newsocmediapost.title)
        print(x.tweet_url)
        return stack
    else:
        print('Stack Empty!')
        return stack


mapstackold = postsocmedia(mapstackold)

# Post another map if the stack has more than two days worth of maps.
try:
    if mapstackold.size() > 50 and mapstackold.size() % 2 == 0:
        mapstackold = postsocmedia(mapstackold)
except:
    print('mapstack too small')


# Check Messages for new maps to add to Stack
for message in r.inbox.unread():
    newMessage = 'true'
if newMessage is 'false':
    logdict['time'] = time.time()
    logdict['type'] = 'noNewMail'
    addToMongo(logdict)

for message in r.inbox.unread():
    if message.subject == "socmedia":
        logdict['type'] = 'socmediastack'
        logdict['time'] = time.time()
        socmediamap = message.body
        socmediamap = os.linesep.join([s for s in socmediamap.splitlines() if s])  # removes extraneous line breaks
        socmediamap = socmediamap.splitlines()  # Turn submission into a list
        title = None
        try:
            if socmediamap[1]:
                title = socmediamap[1]
        except Exception as e:
            print(e)
            print("No title included")
        if socmediamap[0].startswith("https://redd.it/"):
            for item in urllist:
                if item == socmediamap[0]:
                    print("Duplicate detected!")
                    message.mark_read()
            else:
                newStackObject = StackObject(
                    url=socmediamap[0],
                    title=title
                )
                mapstackold.push(data=newStackObject)
                message.mark_read()

with open('data/socmedia.pkl', 'wb') as f:
    pickle.dump(mapstackold, f)
