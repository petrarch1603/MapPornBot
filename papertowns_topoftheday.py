from functions import *
import datetime

# Post the top /r/MapPorn submission from the last week.

print(datetime.datetime.now())
(subreddit, subtitle, social_media_post) = subreddit_top_post(subreddit='papertowns', time_window='day')
print('/r/' + subreddit)
print(subtitle)
print(social_media_post)


