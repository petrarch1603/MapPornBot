"""These are useful Redditbot functions"""

import classes
import csv
from datetime import timedelta
import GridCollage
import logging
import os
import praw
import random
import requests
from secrets import *
import string
import time
import tweepy


# TODO: add type annotations

# def init_soc_posting():
#     """Initialize Twitter and PRAW"""
#     # TODO: is this function used anywhere in the codebase? can it be deleted?
#     # Reddit Bot Login
#
#     # Twitter Authentication
#     auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
#     auth.set_access_token(access_token, access_secret)
#
#     # PRAW logging stuff
#     handler = logging.StreamHandler()
#     handler.setLevel(logging.DEBUG)
#     logger = logging.getLogger('prawcore')
#     logger.setLevel(logging.DEBUG)
#     logger.addHandler(handler)
#

my_reddit_ID = 'petrarch1603'  # This is the human reddit user name, NOT the bot's user name.


def coin_toss():
    """Give a random number of 1 or 0

    :return: 1 or 0
    :rtype: int

    """
    return random.randint(0, 1)


def create_random_string(char_count):
    """Creates a random string of n characters

    :param char_count:
    :type char_count: int
    :return: random characters
    :rtype: str

    """
    allchar = string.ascii_letters + string.digits
    rand_str = "".join(random.choice(allchar) for _ in range(char_count))
    return rand_str


def count_lines_of_file(fname):
    """Count the number of lines of a file

    :param fname: name of file to be counted
    :type fname: str
    :return: count
    :rtype: int

    """
    return sum(1 for _ in open(fname, 'r'))


def get_time_zone(title_str):
    """Check words in a string and match it to a list of place names with time zones in a CSV
            If nothing is found, defaults to 99

    :param title_str:
    :type title_str: str
    :return: time zone
    :rtype: int

    """
    with open('data/locationsZone.csv', 'r') as f:
        csv_reader = csv.reader(f)
        zonedict = {rows[0].upper(): rows[1] for rows in csv_reader}
    this_zone = 99
    for place in zonedict:
        if place in strip_punc(title_str.upper()):
            this_zone = int(zonedict[place])
    return this_zone


def split_message(message_str):
    """Splits a string with line breaks into a list separated by those line breaks

    :param message_str:
    :type message_str: str
    :return:
    :rtype: list

    """
    message_str = os.linesep.join([s for s in str(message_str).splitlines() if s])
    message_list = message_str.splitlines()
    return message_list


def next_weekday(d, weekday):
    # TODO need to clear this up, it's confusing.
    """From gets the next weekday from today's date

    :param d: today's date as a datetime object
    :type d: obj
    :param weekday:
    :type weekday:
    :return:
    :rtype:
    """
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def bot_disclaimer():
    bot_disclaimer_message = 'This is coming from a bot. If you have any feedback [contact the /r/MapPorn Moderators]' \
                             '(https://www.reddit.com/message/compose/?to=' + my_reddit_ID + \
                             '&subject=MapPorn%20bot%20feedback)' + '\n\n----\n\n ^^^MapPornBot ^^^by ' \
                             '^^^/u/Petrarch1603 ^^^[Github](https://github.com/petrarch1603/MapPornBot)'
    return bot_disclaimer_message


def send_reddit_message_to_self(title, message):
    r = praw.Reddit('bot1')
    r.redditor(my_reddit_ID).message(title, message)


def strip_punc(my_str):
    exclude = set(string.punctuation + '0123456789')
    return ''.join(ch for ch in my_str if ch not in exclude)


def create_time_zone_table(zone_dict):
    time_zone_table = "Time Zone|Map Count\n-|-\n"
    for k, v in zone_dict.items():
        # Zone_dict is a dictionary key: zone, value: quantity of maps in that zone
        if v <= 5:
            time_zone_table += "**{}**|**{}**\n".format(k, v)
        else:
            time_zone_table += "{}|{}\n".format(k, v)
    return time_zone_table + "   \n"


def fails_last_24_report(db_obj):
    current_time = time.time()
    errors = ''
    message = ''
    for i in db_obj.get_fails_previous_24(current_time=current_time):
        my_error = classes.Diagnostic.diag_dict_to_obj(i[2]).concise_diag()
        errors += "**Failure** recorded at {}    \n" \
                  " {}   \n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), my_error)
    if errors == '':
        errors = 'No failures logged in last 24 hours    \n\n'
    message += "    \n***    \n"
    message += errors
    message += "    \n***    \n"
    return message


def success_last_24_report(db_obj):
    successes = ''
    for i in db_obj.get_successes_previous_24(current_time=time.time()):
        my_success = classes.Diagnostic.diag_dict_to_obj(i[2]).concise_diag()
        successes += "**Success** recorded at {}    \n" \
                     " {}    \n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), my_success)
    if successes == '':
        successes = 'No successes logged in last 24 hours    \n'
    return successes + '   \n'


def diagnostics_wrapper(func):
    # TODO Get this diagnostics wrapper function working!!

    def func_wrapper(script):
        """

        :param script:
        :type script:
        """
        my_diag = classes.Diagnostic(script=script)
        try:
            func()
            classes.LoggingDB().add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
        except Exception as e:
            my_diag.traceback = e
            classes.LoggingDB().add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
    return func_wrapper


def advertise_on_socmedia(list_of_urls: list, month_year: str, voting_url: str) -> None:
    """Advertise the contest on social media

    :param list_of_urls: List of urls (strings)
    :type list_of_urls: list
    :param month_year: Month year in the format "November 2018" or "Best of 2018"
    :type month_year: str
    :param voting_url: URL of the contest page on Reddit
    :type voting_url: str

    """
    final_urls = []
    for url in list_of_urls:
        if requests.get(url).status_code == 200:
            final_urls.append(url)
    if len(final_urls) >= 9:
        filepath = GridCollage.create_grid(final_urls[:9], text_content=month_year)
    else:
        imagecount = len([name for name in os.listdir('voteimages/')])
        randraw = random.randint(1, imagecount)
        image_file_name = str(randraw).zfill(2)
        filepath = 'voteimages/' + image_file_name + '.png'

    post_message = ('Vote Now for the ' + month_year + ' Map Contest!' + '\n' + voting_url +
                    '\n#MapPorn #Cartography #Contest')
    try:
        social_media_post = classes.GenericPost(filename=filepath, title=post_message)
        socialmediadict = social_media_post.post_to_all_social()
        send_reddit_message_to_self(title="New Voting Post Posted",
                                    message='A new votingpost.py has been run. Check the post to make'
                                            ' sure the bot did it right.   \nHere\'s the link to the '
                                            'post: ' + voting_url + '   \nHere\'s the social media '
                                            'links:    \n' + str(socialmediadict['tweet_url']))
    except Exception as e:
        send_reddit_message_to_self(title="Could not run advertise_on_socmedia()",
                                    message="Problem encountered: " + str(e))

