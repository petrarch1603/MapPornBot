from backup import upload_file
import classes
import datetime
import functions
import praw
import os
from shutil import copyfile
from test_db import main_test_db
import time


def init():
    global hist_db, journal_db, log_db, r, soc_db
    hist_db = classes.HistoryDB()
    journal_db = classes.JournalDB()
    log_db = classes.LoggingDB()
    r = praw.Reddit('bot1')
    soc_db = classes.SocMediaDB()


def main():
    my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))
    message = "**Daily Status Check**   \n   \n"

    # Check Soc Media DB Fresh Count
    fresh_count = soc_db.fresh_count
    if fresh_count <= 10:
        message += "* *NOTE: ONLY {} FRESH SOC MEDIA MAPS LEFT!* *   \n\n".format(fresh_count)
    else:
        message += "{maps} Maps Left   \nThat's {days} days, {hours} hours of content.    \n\n".format(
            maps=fresh_count,
            days=int(fresh_count/8),
            hours=((fresh_count % 8) * 3)
        )

    # Test Functions
    functions_result = test_functions()
    if functions_result == '':
        message += 'Functions Test Passed    \n'
    else:
        message += 'Functions Test Failed:    \n{}    \n\n'.format(functions_result)
    message += "    \n***    \n"

    # Test database integrity
    message += test_db_integrity()
    message += "    \n***   \n"

    # Create report of quantities for each time zone group
    message += functions.create_time_zone_table(soc_db.zone_dict)

    # Make posts older than a year fresh again
    if soc_db.fresh_count < 20:
        try:
            soc_db.make_fresh_again(current_time=time.time(), limit=10)
        except Exception as e:
            error_message = ("Could not run soc_db.make_fresh_again   \n{}   \n{}    \n".format(str(e), str(type(e))))
            my_diag.traceback = error_message
            my_diag.severity = 2
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
            my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
            print(error_message)

    # Get failures from last 24 hours and report on them
    message += functions.fails_last_24_report(db_obj=log_db)

    # Can get successes from last 24 hours and report on them, but removed it because it is too much text
    # Use the function success_last_24_report(db_obj=log_db) if you'd like to bring it back

    # Check Where in the World
    message += check_where_in_world()

    # Check count of remaining where in world maps
    message += remaining_where_in_world()

    # Post stats on the map contest
    message += check_map_contest()

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
        functions.send_reddit_message_to_self(title="Status Report", message=message)
    except Exception as e:
        message += "Could not send message on Reddit.    \n{}     \n{}".format(str(e), str(type(e)))
        with open('data/daily_status.txt', 'w') as text_file:
            text_file.write(message)

    # Make backup
    try:
        make_backup()
        print("Backing up Database to Google Drive")
    except Exception as e:
        error_message = ("Could not make backup!    \n{}    \n{}   \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Log success of script
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
    my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))
    my_diag.traceback = 'test_function script'

    # Test Functions in Checkinbox.py
    try:    # Test get_time_zone()
        assert functions.get_time_zone('London') == 0
        assert functions.get_time_zone('909523[reteopipgfrtAfrica436i') == 1
        assert functions.get_time_zone('354tp4t[fds..dsfDenverre9sg') == -7
    except AssertionError as e:
        error_message += ("get_time_zone function not working    \n{}    \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)
    random_string = functions.create_random_string(10)
    try:
        assert functions.get_time_zone(random_string) == 99
    except AssertionError as e:
        error_message += ("get_time_zone function not working    \n{}    \n{}    \n".format(str(e), random_string))
        error_message += ("get_time_zone function not working    \n{}    \n".format(str(e)))
        my_diag.traceback = error_message
        my_diag.severity = 1
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic

    try:    # Test split_message()
        assert functions.split_message("https://redd.it/9cmxi1\ntext goes here\n12") == \
               ['https://redd.it/9cmxi1', 'text goes here', '12']
        assert functions.split_message("1\n2\n3") == ['1', '2', '3']
        assert functions.split_message('https://redd.it/9e6vbg') == ['https://redd.it/9e6vbg']
    except AssertionError as e:
        error_message += ("Could not run split_message() function   \n{}   \n\n".format(e))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # Test Functions in functions.py
    try:    # Test create_random_string() function
        for x in range(6, 15, 2):
            assert len(functions.create_random_string(x)) == x
    except AssertionError as e:
        error_message += ("create_random_string() test FAILED    \n{}    \n\n".format(e))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)

        # Leaving this here in case more tests are added below
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))
        print(error_message, my_diag)

    return error_message


def test_db_integrity():
    # Integrity Checks on databases
    init()
    error_message = ''
    my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))
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
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
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
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message)

    # log_db_integrity check
    try:
        log_db_integrity = log_db.check_integrity()
        if log_db_integrity.startswith("PASS"):
            error_message += " {}    \n".format(log_db_integrity)
        else:
            error_message += "* *{}*   \n".format(log_db_integrity)
    except Exception as e:
        print(e)
        error_message += ("Could not do log_db Integrity Test    \n{}    \n{}    \n".format(str(e), str(type(e))))
        my_diag.traceback = error_message
        my_diag.severity = 2
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
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
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))  # Re-initialize the diagnostic
        print(error_message, my_diag)

    return error_message


def check_where_in_world():
    error_message = ''
    for file in os.listdir('WW'):
        fsize = os.stat('WW/' + file).st_size
        try:
            assert fsize <= 3200000
        except AssertionError:
            error_message += 'WhereWorld image files must be smaller than 3.2mb ' \
                             'File: {} is size {}'.format(file, int(fsize / float(1000000)))
    return error_message


def check_map_contest():
    message = ''
    try:
        map_subms = functions.count_lines_of_file('submissions.csv')
        with open('data/votingpostdata.txt', 'r') as f:
            last_contest_raw = f.read()
        last_contest_time = r.submission(id=last_contest_raw).created
        days_since_contest = int((datetime.datetime.now().timestamp() - last_contest_time)/60/60/24)
        message = "**{}** maps submitted for this month's map contest.   \n    \n".format(map_subms)
        if days_since_contest > 45:
            message += "It's been **{}** days since a map contest, " \
                       "perhaps it's time to run the voting post script.    \n    \n"
        else:
            message += "**{}** days since the last map contest.    \n    \n"
    except Exception as e:
        message += 'Could not check map contest, problem with script   \n{}    \n    \n'.format(e)
    return message


def remaining_where_in_world():
    count = 0
    now = datetime.datetime.now()
    this_week = str(now.isocalendar()[1]).zfill(2)
    two_digit_year = now.strftime('%y')
    my_time = (str(two_digit_year) + str(this_week))
    for file in os.listdir('WW'):
        if str(file) == 'submissions.csv' or (str(file)[-3:] != 'png'):
            continue
        my_int = int(file[:-4])
        if my_int > int(my_time):
            count += 1
    if count == 0:
        return "**NO WHERE IN WORLD MAPS LEFT!!!**   \n"
    elif count <= 5:
        return "**Only {} Where in World maps left!!**   \nConsider adding more!!   \n    \n".format(count)
    else:
        return "Remaining Where in World Maps: {}   \n   \n".format(count)


if __name__ == '__main__':
    init()
    main()
