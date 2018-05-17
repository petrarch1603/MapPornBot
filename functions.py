# These are useful Redditbot functions

import csv
import datetime
from datetime import datetime, timedelta
import facebook
import fnmatch
import logging
import os
import praw
import random
import re
import requests
from secrets import *
import shutil
from secret_tumblr import *
import tweepy
import signal
import json
import pymongo

# Reddit Bot Login
r = praw.Reddit('bot1')
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

# PRAW logging stuff
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger = logging.getLogger('prawcore')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


my_reddit_ID = 'petrarch1603'  # This is the human reddit user name, NOT the bot's user name.


def shotgun_blast(raw_id_input, announce_input=None, title=None):
    if announce_input != None:
        announce = str(announce_input)
        announce_len = len(announce)
    else:
        announce = ''
        announce_len = 0
    twitter_char_len = (200-announce_len)  # 106 puts the len(messageshort) right at 140
    (url, messageshort, raw_id, messagelong) = parse_reddit(raw_id_input, twitter_char_len)
    if title != None:
        messagelong = title
        messageshort = title[:twitter_char_len]
    shortlink = str('https://redd.it/' + str(raw_id))
    titlelength = len(messagelong)
    ellips = ''
    if titlelength > 106:
        hashtag = ' #mapporn'
    else:
        if titlelength < 77:
            hashtag = ' #Mapping #Cartography'
        else:
            hashtag = ' #Mapping'
    messagelong = announce + messagelong + '\n' + shortlink + '\n#MapPorn #Mapping'
    # print(announce + messageshort + ellips + hashtag)
    # if len(messageshort) <= 109:
    #     charactersLeft = (119-int(len(messageshort)))
    #     print("Would you like to add another hashtag? You have " + str(charactersLeft) + ' characters left:')
    #     extraHashtag = inputHashtagWithTimeout()
    #     if extraHashtag is None:
    #         pass
    #     elif len(extraHashtag) < charactersLeft:
    #         messageshort = (messageshort + ' ' + extraHashtag)
    #         print(messageshort)
    #     else:
    #         pass
    messageshort = announce + '\n' + messageshort + '\n' + shortlink
    print(messageshort)
    # print('Message Long = ' + str(messagelong) + ' (' + str(len(messagelong)) + ')')
    xy = post_from_reddit(url=url, messageshort=messageshort, raw_id=raw_id, messagelong=messagelong)
    return xy


def parse_reddit(raw_id, twitter_char_limit):
    title = remove_text_inside_brackets(str(raw_id.title))
    url = raw_id.url
    messageshort = title[:twitter_char_limit]
    if len(messageshort) < twitter_char_limit:
        twitted_message = message_for_twitter(message=messageshort, twitter_char_limit=twitter_char_limit)
    else:
        twitted_message = messageshort
    raw_id = raw_id
    messagelong = title
    return url, twitted_message, raw_id, messagelong


def remove_text_inside_brackets(text, brackets="[]"):
    count = [0] * (len(brackets) // 2)  # count open/close brackets
    saved_chars = []
    for character in text:
        for i, b in enumerate(brackets):
            if character == b:  # found bracket
                kind, is_close = divmod(i, 2)
                count[kind] += (-1)**is_close  # `+1`: open, `-1`: close
                if count[kind] < 0:  # unbalanced bracket
                    count[kind] = 0  # keep it
                else:  # found bracket to remove
                    break
        else:  # character is not a [balanced] bracket
            if not any(count):  # outside brackets
                saved_chars.append(character)
    return ''.join(saved_chars)


# A function to shorten or extend a string for posting to Twitter
def message_for_twitter(message, twitter_char_limit):
    raw_length = len(message)
    if raw_length < twitter_char_limit:
        message = message + ' #MapPorn'
        message = hashtag_locations(message, twitter_char_limit=twitter_char_limit)
        return message
    else:
        message = ((message[:108]) + '…')
        return message


class SocialMediaPost(object):
    def __init__(self, tweet_url, tumblr_url, facebook_url, message):
        self.tweet_url = tweet_url
        self.tumblr_url = tumblr_url
        self.facebook_url = facebook_url
        self.message = message


def post_to_all_social(filename, messageshort, url, messagelong):
    tweeted = api.update_with_media(filename, status=messageshort)  # Post to Twitter
    tweet_id = str(tweeted._json['id'])  # This took way too long to figure out.
    tumbld = client.create_photo('mappornofficial',
                                 state="published",
                                 tags=['#mapporn'],  # Post to Tumblr
                                 caption=messagelong + ' ' + url,
                                 source=url)
    try:
        tumbld_url = tumbld['id']
        tumbld_url = ('http://mappornofficial.tumblr.com/post/' + str(tumbld_url))
    except Exception as e:
        tumbld_url = "Error encountered: " + str(e)
    fb_url = facebook_image_generic(filename, messagelong)  # Post to Facebook
    tweet_url = ('https://twitter.com/MapPornTweet/status/' + tweet_id)
    socialmediaobject = SocialMediaPost(
        tweet_url=tweet_url,
        tumblr_url=tumbld_url,
        facebook_url=fb_url,
        message=messageshort)
    return socialmediaobject


def post_from_reddit(url, messageshort, raw_id, messagelong):
    filename = 'temp.jpg'
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)
        filesize = os.path.getsize('temp.jpg')
        if filesize > 3070000:
            os.remove(filename)
            filename = 'temp.jpg'
            submission = r.submission(id=raw_id)
            url = submission.preview['images'][0]['resolutions'][3]['url']  # This is the smaller image. Using this because Twitter doesn't like huge files.
            request = requests.get(url, stream=True)
            if request.status_code == 200:
                with open(filename, 'wb') as image:
                    for chunk in request:
                        image.write(chunk)
                abc = post_to_all_social(filename=filename,
                                         messageshort=messageshort,
                                         url=url,
                                         messagelong=messagelong)
                os.remove(filename)
                return abc
            else:
                return str('Unable to download photo')
        else:
            abc = post_to_all_social(filename, messageshort, url, messagelong)
            os.remove(filename)
            return abc
    else:
        return str("Unable to download image")


def tumblr_image(url, message, shortlink):
    client.create_photo('mappornofficial',
                        state="published",
                        tags=['#mapporn'],
                        caption=message + ' ' + shortlink,
                        source=url)


class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def tweet_image_generic(imagefile, message):
    tweeted = api.update_with_media(imagefile, status=message)  # Post to Twitter
    tweet_id = str(tweeted._json['id'])  # This took way too long to figure out.
    tweet_url = 'https://twitter.com/MapPornTweet/status/' + tweet_id
    return tweet_url


def facebook_image_generic(imagefile, message):
    # This was bloody difficult. There are apparently two access tokens. One is good for 60 days, one is good for two hours.
    # If I use the 60 day access token, it posts to Facebook under my personal name. That's no bueno.
    # I wrote a GET request to get the two hour token. That's the bloody_access_token.
    # This token will post as just simply /r/MapPorn, no personal info.
    # !! Some time in January this code will stop working because the 60 days is up. !!
    # When that happens go to 'https://developers.facebook.com/tools/accesstoken/'
    # Click on Debug User Token
    # On the next page at the bottom there should be an option to extend the Access Token
    # In the url just below there is some code access_token=...
    # Change the gibberish in there now to the new access_token you just copied. #
    # Note: Expand the above notest for important info about Facebook access tokens
    rq = requests.get(
       'https://graph.facebook.com/v2.11/me/accounts?access_token=EAAB5zddLiesBABHZB9iOgZAmuuapdSvLvfmwB2jkDvxjFySOOXeMdRDozYkAZAaxMNGUT8EMNZABtIgTmC8tDgIzYoleEAK5g7EN8k73YdD80Ic1FPUTp3NZBkofGYgzM802KNA3JenjYRUGJ27vKQTV2RF1ZB3fGNSUNxs1bMwwZDZD%27')
    stuff = rq.json()
    bloody_access_token = (stuff['data'][0]['access_token'])
    graph = facebook.GraphAPI(access_token=bloody_access_token)
    faced = graph.put_photo(image=open(imagefile, 'rb').read(), message=message)
    fb_post_id = faced['post_id']
    fb_post_id = fb_post_id.replace('_', '/')
    fb_url = str('https://www.facebook.com/OfficialMapPorn/photos/rpp.' + str(fb_post_id))
    return fb_url


def tumblr_image_generic(imagefile, message):
    tumbld = client.create_photo('mappornofficial',
                                 state="published",
                                 tags=['#mapporn'],  # Post to Tumblr
                                 caption=message, data=imagefile)
    tumbld_url = tumbld['id']
    tumbld_url = ('http://mappornofficial.tumblr.com/post/' + str(tumbld_url))
    return tumbld_url


def generic_post(imagefile, message):
    tweet_url = tweet_image_generic(imagefile, message)
    tumbld_url = tumblr_image_generic(imagefile, message)
    fb_url = facebook_image_generic(imagefile, message)
    socialmediaobject = SocialMediaPost(
        tweet_url=tweet_url,
        tumblr_url=tumbld_url,
        facebook_url=fb_url,
        message=message)
    generic_message = ("Tweet Url: " + str(tweet_url) + "   \n"
                       + "Tumblr URL: " + str(tumbld_url) + "   \n" + "Facebook URL: " + str(fb_url))
    return socialmediaobject


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def subreddit_top_post(subreddit, time_window):
    top = r.subreddit(subreddit).top(time_window, limit=1)
    top = list(top)
    top_week = (top[0])
    social_media_post = shotgun_blast(raw_id_input=top_week, announce_input='')
    sub = r.submission(id=top_week)
    return subreddit, sub.title, social_media_post


# A function to take a string, search the locations.txt file for a matching string and add a
# hashtag to the string.
def hashtag_locations(message, twitter_char_limit):
    messageLen = len(message)
    term = message.split(' ')
    LocationsText = open('data/locations.txt').read()
    LocationsText = LocationsText.split()
    for s in term:
        s = str(s)
        if s in LocationsText:
            if messageLen + len(s) <= twitter_char_limit:
                message = message + ' #' + s
                messageLen = messageLen + len(s)
    return message


def bot_disclaimer():
    bot_disclaimer_message = 'This is coming from a bot. If you have any feedback [contact the /r/MapPorn Moderators]' \
                             '(https://www.reddit.com/message/compose/?to=' + my_reddit_ID + \
                             '&subject=MapPorn%20bot%20feedback)' + '\n\n----\n\n ^^^MapPornBot ^^^by ^^^/u/Petrarch1603 ^^^[Github](https://github.com/petrarch1603/MapPornBot)'
    return bot_disclaimer_message


def send_reddit_message_to_self(title, message):
    r.redditor(my_reddit_ID).message(title, message)


class SubmissionObject(object):
    def __init__(self, map_name, map_url, map_desc, creator, unique_message):
        self.map_name = map_name
        self.map_url = map_url
        self.map_desc = map_desc
        self.creator = creator
        self.unique_message = unique_message

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class StackObject(object):
    def __init__(self, url, title=''):
        self.url = url
        self.title = title

class Stack:
    def __init__(self):
        self.stack = list()

    def push(self, data):
        if data not in self.stack:
            self.stack.append(data)
            return True
        return False

    def pop(self):
        if len(self.stack)<=0:
            return ("Stack Empty!")
        return self.stack.pop()

    def size(self):
        return len(self.stack)



def addToMongo(logdictObject):
    connection = pymongo.MongoClient("mongodb://" + mongo_id + ":" + mongo_pw + mongo_db)
    db = connection.mappornstatus
    post_id = db.mappornstatus.insert_one(logdictObject).inserted_id
    print(post_id)





