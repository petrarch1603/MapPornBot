# This is a script that runs weekly on the RaspPi.
# The script will post an advertisement to submit a map to the map contest.
# It will post to multiple social media accounts simultaneously.
# There are two parts of the post: an image and the message.
# The image will be randomly picked from a sub-folder for containing only those images.

import os
import random
import fnmatch
from functions import *
import time
# from PIL import Image # This is only for testing

logdict = {'type': 'socmediapost'}

# Create a random number for choosing image
os.chdir('submitimages')
imagecount = len([name for name in os.listdir('.') if os.path.isfile(name)])  # counts how many images are in the directory
randraw = random.randint(1, (imagecount - 1))  # The count above is wrong by one - maybe includes the .. path, so we need to subtract one
image_file_name = str(randraw).zfill(2)  # This returns a random number with a leading zero if necessary. (i.e. 02 instead of 2)


# Now we need to make the two digit string correspond to a file name in current directory.
# Sometimes the image will be a png or jpg or jpeg etc, this will find the extension and return the whole filename.
image_file_name = fnmatch.filter(os.listdir('.'), image_file_name + '.*')  # This looks in the directory and creates a list of files with the name of the image.
image_file = image_file_name[0]  # There should only be one image with that name, so this returns the name of that file.


# im = Image.open(image_file_name) # This is to test if an image can be opened.
# im.show()

message = "Now taking entries for the /r/MapPorn Monthly Map Contest\nSubmit a map here:\nhttps://www.reddit.com/r/MapPorn/wiki/meta/contest#wiki_submit_a_map"

try:
    social_media_post = generic_post(image_file, message)
    logdict['time'] = time.time()
    logobject = {'script': 'Advertisement for Map Contest',
                 'message': str(social_media_post.message),
                 'tweet_url': str(social_media_post.tweet_url),
                 'tumblr_url': str(social_media_post.tumblr_url),
                 'fb_url': str(social_media_post.facebook_url)}
    logdict['object'] = logobject
    addToMongo(logdict)
except Exception as ex:
    logdict['time'] = time.time()
    logdict['error'] = str(ex)
    addToMongo(logdict)
