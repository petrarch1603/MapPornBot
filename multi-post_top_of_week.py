from classes import *
from functions import *
import os

# Post the top /r/MapPorn submission from the last week.

r = praw.Reddit('bot1')
my_diag = Diagnostic(script=str(os.path.basename(__file__)))
log_db = LoggingDB()

try:
    top_week = list(r.subreddit('mapporn').top('week', limit=1))[0]
    announce_week = 'Top post of the week:\n'
    my_diag.raw_id = top_week.id
    s_b = ShotgunBlast(praw_obj=top_week, announce_input=announce_week)
    assert s_b.check_integrity() == "PASS"
    s_b_dict = s_b.post_to_all_social()
    my_diag.tweet = s_b_dict['tweet_url']
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)

except tweepy.TweepError as e:
    error_message = "Problem with tweepy    \n{}    \n\n".format(e)
    my_diag.severity = 2
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)

except AssertionError as e:
    my_diag.traceback = "Could not run {} script    \n{}   \n\n".format(str(os.path.basename(__file__)), e)
    my_diag.severity = 2
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
