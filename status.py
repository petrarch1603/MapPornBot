from classes import *
from functions import send_reddit_message_to_self
import praw
import os
import time


def init():
    global hist_db, log_db, r, soc_db
    print("Running {}".format(str(os.path.basename(__file__))))
    hist_db = HistoryDB()
    log_db = LoggingDB()
    r = praw.Reddit('bot1')
    soc_db = SocMediaDB()


def main():
    my_diag = Diagnostic(script=str(os.path.basename(__file__)))
    message = "#Daily Status Check\n***\n"
    time_zone_table = "#Time Zone Analysis\n**Time Zone**|**Map Count**\n-----------|------------\n"
    try:
        hist_db_integrity = hist_db.check_integrity()
        if hist_db_integrity.startswith("PASS"):
            message += "* {}\n".format(hist_db_integrity)
        else:
            message += "* *{}*\n".format(hist_db_integrity)
    except Exception as e:
        error_message = ("Could not do hist_db Integrity Test\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))
    try:
        soc_db_integrity = soc_db.check_integrity()
        if soc_db_integrity.startswith("PASS"):
            message += "* {}\n".format(soc_db_integrity)
        else:
            message += "* *{}*\n".format(soc_db_integrity)
    except Exception as e:
        error_message = ("Could not do soc_db Integrity Test\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))

    message += "***\n"

    try:
        for k, v in soc_db.zone_dict.items():
            if v <= 5:
                time_zone_table += "**{}**|**{}**\n".format(k, v)
            else:
                time_zone_table += "{}|{}\n".format(k, v)
        message += time_zone_table + "***\n"
    except Exception as e:
        error_message = ("Could not create time zone table\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))

    try:
        soc_db.make_fresh_again(current_time=time.time())
    except Exception as e:
        error_message = ("Could not run soc_db.make_fresh_again\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))

    try:
        # TODO: Make the failures into a well formatted table like the time zones
        errors = ''
        for i in log_db.get_fails_previous_24(current_time=time.time()):
            errors += "**Failure** recorded at {}\n" \
                      " {}\n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), i[2])
        if errors == '':
            errors = 'No errors logged in last 24 hours\n'
        message += "***"
        message += errors
        message += "***"
    except Exception as e:
        error_message = ("Could not run log_db.get_fails_previous_24\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))

    try:
        successes = ''
        for i in log_db.get_successes_previous_24(current_time=time.time()):
            successes += "**Success** recorded at {}\n" \
                      " {}\n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), i[2])
        if successes == '':
            successes = 'No scripts logged in last 24 hours\n'
        message += successes
    except Exception as e:
        error_message = ("Could not run log_db.get_successes_previous_24\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))

    send_reddit_message_to_self(title="Status Report", message=message)
    hist_db.close()
    soc_db.close()
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
    log_db.close()


init()
main()
