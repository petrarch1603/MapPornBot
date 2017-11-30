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
print("\n")
print("\n")
print(paste)
input('Press enter if this is the shortlink, otherwise press Ctrl+C to quit')
raw_id_input = paste[-6:]  # This takes the last 6 characters of the shortlink URL which is also a unique ID
raw_id_input = r.submission(id=raw_id_input)
feg = shotgun_blast(raw_id_input, '')
print(feg)
