from functions import *

# Post the top /r/MapPorn submission from the last month.
top = r.subreddit('mapporn').top('month', limit=1)
top = list(top)
top_month = (top[0])
announce_month = 'Top post of the month:\n'
shotgun_blast(raw_id_input=top_month, announce_input=announce_month)
