from backup import upload_file
from checkinbox import get_time_zone, split_message
from classes import *
from functions import create_random_string, send_reddit_message_to_self
import praw
import os
from shutil import copyfile
from test_db import main_test_db
import time


def init():
    global hist_db, journal_db, log_db, r, soc_db
    hist_db = HistoryDB()
    journal_db = JournalDB()
    log_db = LoggingDB()
    r = praw.Reddit('bot1')
    soc_db = SocMediaDB()


def main():
    my_diag = Diagnostic(script=str(os.path.basename(__file__)))
    message = "**Daily Status Check**   \n   \n"
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

    functions_result = test_functions()

    if functions_result == '':
        message += 'Functions Test Passed    \n'
    else:
        message += 'Functions Test Failed:    \n{}    \n\n'.format(functions_result)

    message += "    \n***    \n"

    message += test_db_integrity()

    message += "    \n***   \n"

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
        error_message = ("Could not create time zone table   \n{}   \n{}    \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Make posts older than a year fresh again
    try:
        soc_db.make_fresh_again(current_time=time.time())
    except Exception as e:
        error_message = ("Could not run soc_db.make_fresh_again   \n{}   \n{}    \n".format(str(e), str(type(e))))
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
            my_error = Diagnostic.diag_dict_to_obj(i[2]).concise_diag()
            errors += "**Failure** recorded at {}    \n" \
                      " {}   \n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), my_error)
        if errors == '':
            errors = 'No failures logged in last 24 hours    \n\n'
        message += "    \n***    \n"
        message += errors
        message += "    \n***    \n"
    except Exception as e:
        error_message = ("Could not run log_db.get_fails_previous_24    \n{}    \n{}   \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Get successes from last 24 hours and report on them
    try:
        successes = ''
        for i in log_db.get_successes_previous_24(current_time=time.time()):
            my_success = Diagnostic.diag_dict_to_obj(i[2]).concise_diag()
            successes += "**Success** recorded at {}    \n" \
                         " {}    \n".format(time.strftime('%m-%d %H:%M:%S', time.localtime(i[0])), my_success)
        if successes == '':
            successes = 'No successes logged in last 24 hours    \n'
        message += successes
    except Exception as e:
        error_message = ("Could not run log_db.get_successes_previous_24    \n"
                         "{}    \n{}   \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Test the database
    test_db_time, report = main_test_db()

    message += "    \n---------------    \n"
    message += "Test_DB benchmark time = {}   \n".format(test_db_time)
    message += "Total rows in Soc Media DB = {}   \n    \n".format(soc_db.rows_count)
    message += "Total rows in History DB = {}    \n    \n".format(hist_db.rows_count)
    message += report + "    \n"

    # Send results to myself on Reddit
    print(message)
    try:
        send_reddit_message_to_self(title="Status Report", message=message)
    except praw.exceptions.APIException as e:
        message += "Could not send message on Reddit.    \n{}     \n{}".format(str(e), str(type(e)))
        with open('data/daily_status.txt', 'w') as text_file:
            text_file.write(message)
    try:
        make_backup()
        print("Backing up Database to Google Drive")
    except Exception as e:
        error_message = ("Could not make backup!    \n{}    \n{}   \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
    log_db.close()
    journal_db.update_todays_status(benchmark_time=test_db_time)


def make_backup(source_db_path='data/mapporn.db'):
    backup_filename = 'backup' + str(time.strftime("%Y%m%d")) + '.db'
    backup_filepath = 'data/backup/' + backup_filename
    copyfile(source_db_path, backup_filepath)
    upload_file(backup_filepath, backup_filename)


def test_functions():
    init()
    error_message = ''
    my_diag = Diagnostic(script=str(os.path.basename(__file__)))
    my_diag.traceback = 'test_function script'

    # Test Functions in Checkinbox.py
    try:    # Test get_time_zone()
        assert get_time_zone('London') == 0
        assert get_time_zone('909523[reteopipgfrtAfrica436i') == 1
        assert get_time_zone(create_random_string(10)) == 99
        assert get_time_zone('354tp4t[fds..dsfDenverre9sg') == -7
    except AssertionError as e:
        error_message += ("get_time_zone function not working    \n{}    \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)
    try:    # Test split_message()
        assert split_message("https://redd.it/9cmxi1\ntext goes here\n12") == \
               ['https://redd.it/9cmxi1', 'text goes here', '12']
        assert split_message("1\n2\n3") == ['1', '2', '3']
        assert split_message('https://redd.it/9e6vbg') == ['https://redd.it/9e6vbg']
    except AssertionError as e:
        error_message += ("Could not run split_message() function   \n{}   \n\n".format(e))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Test Functions in functions.py
    try:    # Test create_random_string() function
        for x in range(6, 15, 2):
            assert len(create_random_string(x)) == x
    except AssertionError as e:
        error_message += ("create_random_string() test FAILED    \n{}    \n\n".format(e))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)

        # Leaving this here in case more tests are added below
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))
        print(error_message)

    return error_message


def test_db_integrity():
    # Integrity Checks on databases
    init()
    error_message = ''
    my_diag = Diagnostic(script=str(os.path.basename(__file__)))
    my_diag.traceback = 'test_db_integrity script'

    # hist_db_integrity check
    try:
        hist_db_integrity = hist_db.check_integrity()
        if hist_db_integrity.startswith("PASS"):
            error_message += " {}    \n".format(hist_db_integrity)
        else:
            error_message += "* *{}*   \n".format(hist_db_integrity)
    except Exception as e:
        error_message += ("Could not do hist_db Integrity Test    \n{}    \n{}".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # soc_db_integrity check
    try:
        soc_db_integrity = soc_db.check_integrity()
        if soc_db_integrity.startswith("PASS"):
            error_message += " {}   \n".format(soc_db_integrity)
        else:
            error_message += "* *{}*   \n".format(soc_db_integrity)
    except Exception as e:
        error_message += ("Could not do soc_db Integrity Test   \n{}    \n{}    \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # log_db_integrity check
    try:
        log_db_integrity = log_db.check_integrity()
        if log_db_integrity.startswith("PASS"):
            error_message += " {}    \n".format(log_db_integrity)
        else:
            error_message += "* *{}*   \n".format(log_db_integrity)
    except Exception as e:
        error_message += ("Could not do log_db Integrity Test    \n{}    \n{}    \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # jour_db_integrity check
    try:
        jour_db_integrity = journal_db.check_integrity()
        if jour_db_integrity.startswith("PASS"):
            error_message += " {}    \n".format(jour_db_integrity)
        else:
            error_message += "* *{}*   \n".format(jour_db_integrity)
    except Exception as e:
        error_message += ("Could not do journal_db Integrity Test\n{}\n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    return error_message


if __name__ == '__main__':
    init()
    main()
