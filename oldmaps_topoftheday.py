from functions import *

(subreddit, subtitle, social_media_post) = subreddit_top_post(subreddit='oldmaps', time_window='week')

print('/r/' + subreddit)
print(subtitle)
print(social_media_post)
