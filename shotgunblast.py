#!python

# Shotgun Blast is a Python script to post a Reddit image to
# multiple social networks simultaneously

# Users must copy the reddit shortlink to their clipboard:
# Shortlinks look like this: https://redd.it/abc123

# When the program runs it will post the image from that shortlink, along with the title
# and the shortlink to Twitter and Tumblr.


import pyperclip
from functions import *

paste = pyperclip.paste()
if paste.startswith("https://redd.it/"):
    pass
else:
    print("That is not a Reddit shortlink")
    exit()
print("\n")
print("\n")
print(paste)
raw_id_input = paste[-6:]  # This takes the last 6 characters of the shortlink URL which is also a unique ID
raw_id_input = r.submission(id=raw_id_input)
socialmediaobject = shotgun_blast(raw_id_input, '')
print(socialmediaobject.message)
print('Tweet ' + socialmediaobject.tweet_url)
print('Tumblr ' + socialmediaobject.tumblr_url)
print('Facebook ' + socialmediaobject.facebook_url)