# This is a project to have a weekly social media trivia post. This python script will
# run a bot that posts a map image to social media and users will guess the location of
# the map. The idea is to post it every Wednesday, hence the name "Where in the world
# Wednesday."

import time
from functions import *
import datetime
import os


post_message = "#WhereInTheWorld #MapPorn\n" \
          "Every week we bring you a map of an unknown location. " \
          "If you know where it's at, reply in the comments!\n" \
          "More info at https://t.co/yCv6Ynqa4u"


# Get the week and year as a format for indexing image
now = datetime.datetime.now()
thisweek = str(now.isocalendar()[1]).zfill(2)
two_digit_year = now.strftime('%y')
image_number = (str(two_digit_year) + str(thisweek))
image_file_name = (image_number + '.png')


# Post to Social Media
os.chdir('WW')
logdict = {'type': 'socmediapost'}
try:
    social_media_post = generic_post(imagefile=image_file_name, message=post_message)
    logdict['time'] = time.time()
    logobject = {'script': 'Top Post of Month',
                 'message': social_media_post.message,
                 'tweet_url': social_media_post.tweet_url,
                 'tumblr_url': social_media_post.tumblr_url,
                 'fb_url': social_media_post.facebook_url}
    logdict['object'] = logobject
    addToMongo(logdict)
    os.chdir('..')
    with open('/data/locations.csv') as current_csv:
        csvreader = csv.reader(current_csv)
        for row in csvreader:
            if image_number == row[0]:
                true_location = row[1]
                print("True Location is: " + true_location)
                r.redditor(my_reddit_ID).message(
                    "Where in the World Trivia Contest",
                    'Where in the World is now live!\nThe correct location is: ' + true_location +
                    '\nThe Twitter thread is here: ' + str(social_media_post.tweet_url))
except Exception as ex:
    os.chdir('..')
    print(ex)
    logdict['time'] = time.time()
    logdict['error'] = str(ex)
    logobject = {'script': 'Top Post of Month'}
    logdict['object'] = logobject
    addToMongo(logdict)



