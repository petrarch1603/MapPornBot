"""Tests the database

Script for checking the database class. This is more thorough than the check integriy methods in each
database because it will interact and change data in each database. For that reason this script copies
the live database and runs the methods on a copy. The original database remains unchanged.

"""

import checkinbox
import classes
import functions
import os
import random
from shutil import copyfile
import time

# Script for checking the database class. This is more thorough than the check integriy methods in each
# database because it will interact and change data in each database. For that reason this script copies
# the live database and runs the methods on a copy. The original database remains unchanged.

source_db_path = 'data/mapporn.db'
test_db_path = 'data/test.db'
copyfile(source_db_path, test_db_path)


class MockMessage:
    """Mock class for creating a message object for testing the checkinbox.py script"""

    def __init__(self, body: str = 'abc', author: str = 'abc', subject: str = 'abc', raw_id: str = 'abcdef') -> None:
        self.body = body
        self.author = author
        self.subject = subject
        self.id = raw_id

    def __repr__(self):
        return self.id

    def __str__(self):
        return self.id

    def mark_read(self):
        pass

    def reply(self, text):
        pass


def init() -> None:
    """Initializes test databases for testing"""
    global test_hist_db, test_log_db, test_soc_db, test_jour_db, test_db_list, test_cont_db
    test_hist_db = classes.HistoryDB(path=test_db_path)
    test_log_db = classes.LoggingDB(path=test_db_path)
    test_soc_db = classes.SocMediaDB(path=test_db_path)
    test_jour_db = classes.JournalDB(path=test_db_path)
    test_cont_db = classes.ContestDB(path=test_db_path)
    test_db_list = [test_hist_db, test_log_db, test_soc_db, test_jour_db, test_cont_db]


def test_close_all():
    """Closes all databases"""
    for db in test_db_list:
        try:
            db.close()
        except classes.sqlite3.ProgrammingError as e:
            if str(e) == "Cannot operate on a closed database.":
                print('Closed Database')
            else:
                raise Exception


def test_check_integrity() -> str:
    """Checks the integrity of test databases

    :return: Status report
    :rtype: str

    """
    init()
    print("Checking Database Integrity")
    report = ''
    for i in test_db_list:
        check = i.check_integrity()
        if not check.startswith('PASS'):
            report += check
    test_close_all()
    return report


def test_row_count(delta: int = 0) -> None:
    """ Checks the row count of all the row counts.

    The script will add rows to the database, therefore there needs to be a delta so the script
    can verify the new count is correct.

    :param delta: Number of changed rows
    :type delta: int

    """

    init()
    # Check that row count of test_db's are equal to length of .all_rows_list() method
    assert test_hist_db_old_count + delta == len(test_hist_db.all_rows_list())
    assert test_log_db_old_count + delta == len(test_log_db.all_rows_list())
    assert test_soc_db_old_count + delta == len(test_soc_db.all_rows_list())
    assert test_jour_db_old_count + delta == len(test_jour_db.all_rows_list())
    test_close_all()


def test_days_in_history() -> None:
    """Tests the HistoryDB"""
    init()
    # Check the change_date() method works
    # Get five random raw_ids and five random dates
    raw_ids_dict = {}
    for _ in range(5):
        raw_ids_dict[test_hist_db.get_random_row()[0].raw_id] = \
            (random.randint(1, 365))

    # Change dates on the five raw_ids to the new random dates
    for k, v in raw_ids_dict.items():
        test_hist_db.change_date(raw_id=k, new_date=v)
    # Re-initialize database and make sure the row counts match
    test_close_all()
    init()
    test_row_count()
    init()

    # Check that the five raw_ids have the new random dates
    for my_raw_id, date in raw_ids_dict.items():
        maprow_list = test_hist_db.get_rows_by_date(date=date)
        # Check every object in list and make sure at least one has the raw_id
        assert any(i.raw_id == my_raw_id for i in maprow_list)
    test_close_all()


def test_time_zone(count: int = 5) -> None:
    """Change the time zones on five random raw_ids

    :type count: int

    """
    init()
    print("Testing SocMediaDB time zones.")
    # Get five random raw_ids
    raw_ids_dict = {}
    for _ in range(count):
        random_zone = random.randint(-10, 12)
        random_zone_list = test_soc_db.get_rows_by_time_zone(time_zone=random_zone, fresh='0 OR 1')
        if len(random_zone_list) > 0:
            random_index = random.randint(1, len(random_zone_list) - 1)
        else:
            random_zone = 99
            random_index = random.randint(1, len(test_soc_db.get_rows_by_time_zone(time_zone=random_zone)) - 1)
        assert isinstance(test_soc_db.get_rows_by_time_zone(time_zone=random_zone), list)
        raw_ids_dict[random_zone_list[random_index].raw_id] = random_zone

    # Change time zones for five random raw_ids
    for k, v in raw_ids_dict.items():
        test_soc_db.change_time_zone(raw_id=k, new_zone=v)
    # Re-initialize database and make sure row counts match
    test_close_all()
    init()
    test_row_count()
    # Check that the five raw_ids have the new random dates
    init()
    for k, v in raw_ids_dict.items():  # k is a raw_id, v is a time_zone
        found = False
        my_list = test_soc_db.get_rows_by_time_zone(time_zone=v, fresh='0 OR 1')
        while found is not True:
            for i in my_list:
                if i.raw_id == k:
                    found = True
            assert found is True
    test_close_all()
    init()


def test_update_to_not_fresh() -> None:
    """Tests the method for updating row to not fresh"""
    # Testing SocDB method for making not fresh
    init()
    my_list = []
    for _ in range(5):
        random_index = random.randint(1, (len(test_soc_db) - 1))
        my_list.append(test_soc_db.all_rows_list()[random_index].raw_id)
    for i in my_list:
        test_soc_db.update_to_not_fresh(raw_id=i)
    # Re-initialize database
    test_close_all()
    init()
    test_row_count()
    # Check that the five raw_ids are not fresh
    init()
    all_rows = test_soc_db.all_rows_list()
    for i in my_list:
        for j in all_rows:
            if j.raw_id == i:
                assert j.fresh == 0
    test_close_all()


def test_make_fresh_again(limit: int = 100) -> None:
    """Tests the method for changing row from un-fresh to fresh

    :param limit: A limit to how many rows the function should make fresh again
    :type limit: int

    """
    print("Testing making fresh again")
    init()
    # for i in test_soc_db.all_rows_list():
    #     test_soc_db.curs.execute("UPDATE {} SET date_posted={} WHERE raw_id='{}'".format('socmediamaps',
    #                                                                                      time.time(),
    #                                                                                      i[0]))
    current_fresh_count = test_soc_db.fresh_count
    test_soc_db.make_fresh_again(current_time=9999999999, limit=limit)
    init()
    assert test_soc_db.fresh_count == current_fresh_count + limit
    test_close_all()


def test_add_entries(num_of_entries: int) -> None:
    """Tests methods for adding entries to database

    :param num_of_entries: How many entries to add
    :type num_of_entries: int

    """
    # Add random new entries to database
    init()
    print("Adding {} random entries to all databases for testing...".format(
        str(num_of_entries)))
    for _ in range(num_of_entries):
        rand_hist_id = functions.create_random_string(6)
        rand_soc_id = functions.create_random_string(6)
        rand_title = functions.create_random_string(10)
        rand_log_text = functions.create_random_string(11)
        rand_boolean = random.randint(0, 1)
        test_hist_db.add_row_to_db(raw_id=rand_hist_id,
                                   text=functions.create_random_string(10),
                                   day_of_year=random.randint(1, 365))
        my_diag_dic = classes.Diagnostic(script=(functions.create_random_string(8)) + '.py')
        my_diag_dic.raw_id = functions.create_random_string(6)
        my_diag_dic.severity = random.randint(1, 9)
        my_diag_dic.table = functions.create_random_string(6)
        my_diag_dic.traceback = functions.create_random_string(15)
        my_diag_dic.tweet = "http://" + str(functions.create_random_string(8))
        my_diag_dic.title = rand_title
        test_log_db.add_row_to_db(diagnostics=my_diag_dic.make_dict(),
                                  error_text=rand_log_text,
                                  passfail=rand_boolean)
        init()

        # Integrity checks will make sure all fresh == 0 rows include a date_posted.
        # This logic ensures that test won't fail.
        if rand_boolean == 0:
            date_posted = time.time()
        else:
            date_posted = 'NULL'
        test_soc_db.add_row_to_db(raw_id=rand_soc_id,
                                  text=functions.create_random_string(11),
                                  time_zone=random.randint(-10, 12),
                                  fresh=rand_boolean,
                                  date_posted=date_posted)
        test_jour_db.update_todays_status(benchmark_time=.5)
        test_close_all()
        init()
        if rand_boolean == 0:
            assert rand_log_text in str(test_log_db.get_fails_previous_24(current_time=time.time()))
            # TODO make a better assertion for checking diagnositcs in previous 24 hours
            assert my_diag_dic.raw_id in str(test_log_db.get_fails_previous_24(current_time=time.time()))
        elif rand_boolean == 1:
            assert rand_log_text in str(test_log_db.get_successes_previous_24(current_time=time.time()))
            assert my_diag_dic.raw_id in str(test_log_db.get_successes_previous_24(current_time=time.time()))
        assert test_soc_db.check_if_already_in_db(raw_id=rand_soc_id) is True
        assert test_soc_db.check_if_already_in_db(raw_id=rand_hist_id) is False
    test_close_all()
    init()
    test_row_count(delta=num_of_entries)


def test_check_inbox(number_of_tests=5):
    """Tests that check inbox integrates with the database

    :param number_of_tests: How many tests to do
    :type number_of_tests: int

    """
    error_message = ''
    for _ in range(number_of_tests):

        # # Test the contest message
        checkinbox.init(path=test_db_path)
        rand_map_name = functions.create_random_string(10)
        rand_website = 'http://www.' + functions.create_random_string(8) + '.com/' + \
                       functions.create_random_string(7) + '.jpg'
        rand_description = functions.create_random_string(15)
        rand_author = 'Author' + functions.create_random_string(11)
        rand_raw_id = functions.create_random_string(6)
        test_contest_message = "Map Name: {}   \n" \
                               "Link: {}   \n" \
                               "Description: {}".format(rand_map_name,
                                                        rand_website,
                                                        rand_description)

        test_message_obj = MockMessage(body=test_contest_message, author=rand_author, raw_id=rand_raw_id)

        try:
            test_close_all()
            checkinbox.contest_message(message=test_message_obj, path=test_db_path)
            init()
            updated_row = test_cont_db.get_row_by_raw_id(rand_raw_id)
            assert updated_row.map_name == rand_map_name
            assert updated_row.raw_id == rand_raw_id
            assert updated_row.desc == rand_description
            assert updated_row.url == rand_website
            assert updated_row.author == rand_author
            test_cont_db.delete_by_raw_id(rand_raw_id)
            test_close_all()

        except AssertionError as e:
            error_message += "Error when testing contest message.    \n{}".format(e)

        # # Test the socmedia message
        init()
        rand_raw_id = functions.create_random_string(6)
        rand_url = 'https://redd.it/' + rand_raw_id

        test_socmedia_message = rand_url
        rand_title = functions.create_random_string(20)
        test_socmedia_message += "   \n" + rand_title
        fresh_status = functions.coin_toss()
        if fresh_status == 0:
            test_socmedia_message += '   \n' + str(fresh_status)
        test_socmediamsg_obj = MockMessage(body=test_socmedia_message)
        init()
        checkinbox.socmedia_message(message=test_socmediamsg_obj, path=test_db_path)

        try:
            test_close_all()
            init()

            updated_row = test_soc_db.get_row_by_raw_id(rand_raw_id)
            assert updated_row.raw_id == rand_raw_id
            assert updated_row.text == rand_title
            assert updated_row.fresh == fresh_status
            test_soc_db.delete_by_raw_id(rand_raw_id)
        except AssertionError as e:
            error_message += "Error when testing socmedia message.   \n{}".format(e)

        # # Test the dayinhistory message
        rand_day_of_year = str(random.randint(1, 365))
        # Function should work regardless of order, so when testing the order is shuffled.
        test_list = [rand_day_of_year, rand_url, rand_title]
        random.shuffle(test_list)
        test_dayinhistory_message = '   \n'.join(test_list)
        test_dayinhistory_obj = MockMessage(body=test_dayinhistory_message)
        test_close_all()
        init()
        checkinbox.dayinhistory_message(message=test_dayinhistory_obj, path=test_db_path)

        try:
            init()
            updated_row = test_hist_db.get_row_by_raw_id(rand_raw_id)
            assert updated_row.raw_id == rand_raw_id
            assert updated_row.text == rand_title
            assert updated_row.day_of_year == int(rand_day_of_year)
            test_hist_db.delete_by_raw_id(rand_raw_id)
        except AssertionError as e:
            error_message += "Error when testing dayinhistory message   \n{}".format(e)
    return error_message


def test_delete_entry(count=5):
    """Tests that the entry is deleted from database

    :param count: number of entries to delete
    :type count: int

    """
    init()
    error_message = ''
    for i in range(count):
        try:
            my_raw_id = test_soc_db.get_random_row()[0].raw_id
            assert len(test_soc_db.get_row_by_raw_id(my_raw_id).raw_id) == 6
            test_soc_db.delete_by_raw_id(my_raw_id)
            assert test_soc_db.get_row_by_raw_id(my_raw_id) == []
        except AssertionError as e:
            error_message += 'Error testing delete method   \n{}'.format(e)
    return error_message


def main_test_db(num_of_entries=5):
    """Main test of databases

    :param num_of_entries: number of entries to create
    :type num_of_entries:

    """
    t_start = time.perf_counter()
    init()

    # Get count of all rows of each database
    report = test_check_integrity()
    test_row_count()
    test_days_in_history()
    test_time_zone()
    print("Testing update to not fresh")
    test_update_to_not_fresh()
    test_make_fresh_again()

    test_add_entries(num_of_entries=num_of_entries)
    print("Testing delete entry")
    report += test_delete_entry()
    print("Testing Check Inbox functions")
    report += test_check_inbox(number_of_tests=num_of_entries)
    print("Checking DB integrity again.")
    report += test_check_integrity()
    print("Tests Passed, deleting test database")
    os.remove(test_db_path)
    t_stop = time.perf_counter()
    print(t_stop-t_start)
    print(report)
    return t_stop - t_start, report


init()
test_hist_db_old_count = test_hist_db.rows_count
test_log_db_old_count = test_log_db.rows_count
test_soc_db_old_count = test_soc_db.rows_count
test_jour_db_old_count = test_jour_db.rows_count

if __name__ == "__main__":
    main_test_db(5)
