# This is a project to have a weekly social media trivia post. This python script will
# run a bot that posts a map image to social media and users will guess the location of
# the map. The idea is to post it every Wednesday, hence the name "Where in the world
# Wednesday."

from classes import *
import csv
import datetime
from functions import send_reddit_message_to_self
import os


post_message = "#WhereInTheWorld #MapPorn\n" \
          "Every week we bring you a map of an unknown location. " \
          "If you know where it's at, reply in the comments!\n" \
          "More info at https://t.co/yCv6Ynqa4u"

log_db = LoggingDB()
my_diag = Diagnostic(script=str(os.path.basename(__file__)))

try:
    # Get the week and year as a format for indexing image
    now = datetime.datetime.now()
    thisweek = str(now.isocalendar()[1]).zfill(2)
    two_digit_year = now.strftime('%y')
    image_number = (str(two_digit_year) + str(thisweek))
    image_file_name = (image_number + '.png')

    # Post to Social Media
    os.chdir('WW')

    socmediadict = GenericPost(image_file_name, post_message).post_to_all_social()
    my_diag.tweet = socmediadict['tweet_url']
    os.chdir('..')
    with open('/data/locations.csv') as current_csv:
        csvreader = csv.reader(current_csv)
        for row in csvreader:
            if image_number == row[0]:
                true_location = row[1]
                send_reddit_message_to_self(title="Where in world answer", message='The correct location is: ' +
                                                  str(true_location) + '    \nThe Twitter thread is here: ' +
                                                  str(my_diag.tweet))
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)

except tweepy.TweepError as e:
    if str(e) == 'Unable to access file: No such file or directory':
        os.chdir('..')
        error_message = "No where in the world maps left. Add more!     \n{}    \n\n".format(e)
        my_diag.traceback = error_message
        send_reddit_message_to_self(title="No where world maps left", message=error_message)
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)

except Exception as e:
    os.chdir('..')
    my_diag.traceback = "error:    \n{}    \n\n".format(e)
    my_diag.severity = 2
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
