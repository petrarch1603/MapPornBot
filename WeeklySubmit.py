# This is a script that runs weekly on the RaspPi.
# The script will post an advertisement to submit a map to the map contest.
# It will post to multiple social media accounts simultaneously.
# There are two parts of the post: an image and the message.
# The image will be randomly picked from a sub-folder for containing only those images.

from classes import *
import os
import random
import fnmatch
# from functions import *
# import time

log_db = LoggingDB()
my_diag = Diagnostic(script=str(os.path.basename(__file__)))
title = "Now taking entries for the /r/MapPorn Monthly Map Contest\nSubmit a map here:\n" \
            "https://www.reddit.com/r/MapPorn/wiki/meta/contest#wiki_submit_a_map"

try:
    # Create a random number for choosing image
    os.chdir('submitimages')
    imagecount = len([name for name in os.listdir('.') if os.path.isfile(name)])
    # The count above is wrong by one - maybe includes the .. path, so we need to subtract one
    randraw = random.randint(1, (imagecount - 1))
    image_file_name = str(randraw).zfill(2)  # add leading zero if necessary

    # Now we need to make the two digit string correspond to a file name in current directory.
    # Sometimes the image will be a png or jpg or jpeg etc, this will find the extension and return the whole filename.
    image_file_name = fnmatch.filter(os.listdir('.'), image_file_name + '.*')
    image_file = image_file_name[0]
    socmediadict = GenericPost(image_file, title).post_to_all_social()
    my_diag.tweet = socmediadict['tweet_url']
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)

except Exception as e:
    error_message = "Could not run WeeklySubmit.py.   \n{}    \n\n".format(e)
    my_diag.traceback = error_message
    my_diag.severity = 2
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
