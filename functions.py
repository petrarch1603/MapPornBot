# These are useful Redditbot functions


import csv
from datetime import timedelta
import logging
import os
import praw
import random
from secrets import *
import string
import tweepy


def init_soc_posting():
    # Reddit Bot Login
    r = praw.Reddit('bot1')

    # Twitter Authentication
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


def create_random_string(char_count):
    allchar = string.ascii_letters + string.digits
    rand_str = "".join(random.choice(allchar) for _ in range(char_count))
    return rand_str


def count_lines_of_file(fname):
    return sum(1 for _ in open(fname, 'r'))


def get_time_zone(title_str):
    with open('data/locationsZone.csv', 'r') as f:
        csv_reader = csv.reader(f)
        zonedict = {rows[0].upper(): rows[1] for rows in csv_reader}
    this_zone = 99
    for place in zonedict:
        if place in strip_punc(title_str.upper()):
            this_zone = int(zonedict[place])
    return this_zone


def split_message(message_str):
    message_str = os.linesep.join([s for s in str(message_str).splitlines() if s])
    message_list = message_str.splitlines()
    return message_list


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def bot_disclaimer():
    bot_disclaimer_message = 'This is coming from a bot. If you have any feedback [contact the /r/MapPorn Moderators]' \
                             '(https://www.reddit.com/message/compose/?to=' + my_reddit_ID + \
                             '&subject=MapPorn%20bot%20feedback)' + '\n\n----\n\n ^^^MapPornBot ^^^by ^^^/u/Petrarch1603 ^^^[Github](https://github.com/petrarch1603/MapPornBot)'
    return bot_disclaimer_message


def send_reddit_message_to_self(title, message):
    r = praw.Reddit('bot1')
    r.redditor(my_reddit_ID).message(title, message)


def strip_punc(my_str):
    exclude = set(string.punctuation + '0123456789')
    return ''.join(ch for ch in my_str if ch not in exclude)

