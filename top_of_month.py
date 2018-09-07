from classes import *
# from functions import *
import os
import praw

# Post the top /r/MapPorn submission from the last month.

r = praw.Reddit('bot1')
top_month = list(r.subreddit('mapporn').top('month', limit=1))[0]
announce_month = 'Top post of the month:\n'
my_diag = Diagnostic(script=str(os.path.basename(__file__)))
my_diag.raw_id = top_month.id
log_db = LoggingDB()

try:
    s_b = ShotgunBlast(praw_obj=top_month, announce_input=announce_month)
    assert s_b.check_integrity() == "PASS"
    s_b_dict = s_b.post_to_all_social()
    my_diag.tweet = s_b_dict['tweet_url']
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
except Exception as ex:
    my_diag.traceback = "Could not run top_of_month script    \n{}   \n\n".format(ex)
    my_diag.severity = 2
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)