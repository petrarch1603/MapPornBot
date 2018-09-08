from classes import *
from functions import send_reddit_message_to_self
import praw
import os
from test_db import main_test_db
import time


def init():
    global hist_db, journal_db, log_db, r, soc_db
    print("Running {}".format(str(os.path.basename(__file__))))
    hist_db = HistoryDB()
    journal_db = JournalDB()
    log_db = LoggingDB()
    r = praw.Reddit('bot1')
    soc_db = SocMediaDB()


def main():
    my_diag = Diagnostic(script=str(os.path.basename(__file__)))
    message = "Daily Status Check   \n   \n"
    fresh_count = soc_db.fresh_count
    if fresh_count <= 10:
        message += "* *NOTE: ONLY {} FRESH SOC MEDIA MAPS LEFT!* *   \n\n".format(fresh_count)
    else:
        message += "{maps} Maps Left   \nThat's {days} days, {hours} hours of content.    \n\n".format(
            maps=fresh_count,
            days=int(fresh_count/8),
            hours=((fresh_count % 8) * 3)
        )
    time_zone_table = "Time Zone|Map Count\n-|-\n"

    # Integrity Checks on databases
    try:
        hist_db_integrity = hist_db.check_integrity()
        if hist_db_integrity.startswith("PASS"):
            message += " {}    \n".format(hist_db_integrity)
        else:
            message += "* *{}*   \n".format(hist_db_integrity)
    except Exception as e:
        error_message = ("Could not do hist_db Integrity Test\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)
    try:
        soc_db_integrity = soc_db.check_integrity()
        if soc_db_integrity.startswith("PASS"):
            message += " {}   \n".format(soc_db_integrity)
        else:
            message += "* *{}*   \n".format(soc_db_integrity)
    except Exception as e:
        error_message = ("Could not do soc_db Integrity Test   \n{}    \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)
    try:
        log_db_integrity = log_db.check_integrity()
        if log_db_integrity.startswith("PASS"):
            message += " {}    \n".format(log_db_integrity)
        else:
            message += "* *{}*   \n".format(log_db_integrity)
    except Exception as e:
        error_message = ("Could not do log_db Integrity Test\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)
    try:
        jour_db_integrity = journal_db.check_integrity()
        if jour_db_integrity.startswith("PASS"):
            message += " {}    \n".format(jour_db_integrity)
        else:
            message += "* *{}*   \n".format(jour_db_integrity)
    except Exception as e:
        error_message = ("Could not do journal_db Integrity Test\n{}\n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    message += "***   \n"

    # Create report of quantities for each time zone group
    try:
        for k, v in soc_db.zone_dict.items():
            if v <= 5:
                time_zone_table += "{}|{}\n".format(k, v)
            else:
                time_zone_table += "{}|{}\n".format(k, v)
        message += time_zone_table + "   \n"
        print(message)
    except Exception as e:
        error_message = ("Could not create time zone table   \n{}   \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Make posts older than a year fresh again
    try:
        soc_db.make_fresh_again(current_time=time.time())
    except Exception as e:
        error_message = ("Could not run soc_db.make_fresh_again   \n{}   \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Get failures from last 24 hours and report on them
    try:
        # TODO: Make the failures into a well formatted table like the time zones
        errors = ''
        for i in log_db.get_fails_previous_24(current_time=time.time()):
            errors += "**Failure** recorded at {}    \n" \
                      " {}   \n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), i[2])
        if errors == '':
            errors = 'No errors logged in last 24 hours    \n\n'
        message += "    \n***    \n"
        message += errors
        message += "    \n***    \n"
    except Exception as e:
        error_message = ("Could not run log_db.get_fails_previous_24    \n{}    \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Get successes from last 24 hours and report on them
    try:
        successes = ''
        for i in log_db.get_successes_previous_24(current_time=time.time()):
            successes += "**Success** recorded at {}    \n" \
                      " {}    \n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), i[2])
        if successes == '':
            successes = 'No successes logged in last 24 hours    \n'
        message += successes
    except Exception as e:
        error_message = ("Could not run log_db.get_successes_previous_24    \n{}    \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
    log_db.close()

    # Test the database
    test_db_time, report = main_test_db()

    message += "    \n---------------    \n"
    message += "Test_DB benchmark time = {}   \n".format(test_db_time)
    message += "Total rows in Soc Media DB = {}   \n    \n".format(soc_db.rows_count)
    message += "Total rows in History DB = {}    \n    \n".format(hist_db.rows_count)

    # Add result to daily journal database
    message += report + "    \n"
    journal_db.update_todays_status(benchmark_time=test_db_time)

    # Send results to myself on Reddit
    print(message)
    send_reddit_message_to_self(title="Status Report", message=message)


init()
main()

# TODO: Make backups of database when it's successfully executed
