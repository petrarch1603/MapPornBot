# This script spaces out the submissions to social media.
#
# This way I can add multiple social media posts simultaneously and they won't all post at once.
# Instead they will be added as objects to a stack. Every few hours the script will run and submit one social media post
# at a time.

import os
import pickle
import praw
import time
from functions import addToMongo, Stack, StackObject, shotgun_blast

r = praw.Reddit('bot1')
logdict = {}
newMessage = 'false'

with open('socmedia.pkl', 'rb') as f:
    mapstackold = (pickle.load(f))

newsocmediapost = mapstackold.pop()
if newsocmediapost != "Stack Empty!":
    raw_url = str(newsocmediapost.url[-6:])
    redditObject = r.submission(id=raw_url)
    x = shotgun_blast(raw_id_input=(redditObject), title=newsocmediapost.title)
    print(x)
else:
    print('Stack Empty!')

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
        # unique_id = message # Gets the message's unique ID
        try:
            if socmediamap[1]:
                title = socmediamap[1]
        except:
            print("No title included")
        if socmediamap[0].startswith("https://redd.it/"):
            newStackObject = StackObject(
                url=socmediamap[0],
                title=title
            )
            mapstackold.push(data=newStackObject)
        message.mark_read()

with open('socmedia.pkl', 'wb') as f:
    pickle.dump(mapstackold, f)
