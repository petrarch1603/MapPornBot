from functions import *

(subreddit, subtitle, social_media_post) = subreddit_top_post(subreddit='oldmaps', time_window='week')

print('/r/' + subreddit)
print(subtitle)
print(social_media_post)
r.redditor(my_reddit_ID).message(
        'Ran script of top ' + subreddit + 'map of the day',
        'Check that the script executed properly.    \n' + social_media_post +
        '\nIf script executed properly. Delete this message from oldmaps_topoftheday.py')