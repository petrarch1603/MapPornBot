from classes import *
import os
import random
from shutil import copyfile
import string
import time

# Script for checking the database class. This is more thorough than the check integriy methods in each
# database because it will interact and change data in each database. For that reason this script copies
# the live database and runs the methods on a copy.

#TODO add journal testing to this script!
source_db_path = 'data/mapporn.db'
test_db_path = 'data/test.db'
copyfile(source_db_path, test_db_path)


def init():
    global test_hist_db, test_log_db, test_soc_db
    test_hist_db = HistoryDB(path=test_db_path)
    test_log_db = LoggingDB(path=test_db_path)
    test_soc_db = SocMediaDB(path=test_db_path)


    # Get count of all rows of each database
    test_hist_db_old_count = test_hist_db.rows_count
    test_log_db_old_count = test_log_db.rows_count
    test_soc_db_old_count = test_soc_db.rows_count


def test_close_all():
    test_hist_db.close()
    test_log_db.close()
    test_soc_db.close()


def test_check_integrity():
    init()
    print("Checking Database Integrity")
    test_hist_db.check_integrity()
    test_log_db.check_integrity()
    test_soc_db.check_integrity()
    test_close_all()


def create_random_string(char_count):
    allchar = string.ascii_letters + string.digits
    rand_str = "".join(random.choice(allchar) for _ in range(char_count))
    return rand_str


def test_row_count(delta=0):
    print("Testing Row Count")
    # Delta will be to test for changes in count. In some tests the database
    # will be changed and this argument is to verify the new count.

    init()
    # Check that row count is equal to length of .all_rows_list() method
    assert test_hist_db_old_count + delta == len(test_hist_db.all_rows_list())
    assert test_log_db_old_count + delta == len(test_log_db.all_rows_list())
    assert test_soc_db_old_count + delta == len(test_soc_db.all_rows_list())
    test_close_all()


def test_schema():
    print("Testing Schema")
    init()
    # Check that the schema is correct
    assert test_hist_db.schema == OrderedDict([('raw_id', 'TEXT'),
                                               ('text', 'TEXT'),
                                               ('day_of_year', 'NUMERIC')])
    assert test_log_db.schema == OrderedDict([('date', 'NUMERIC'),
                                              ('error_text', 'TEXT'),
                                              ('diagnostics', 'TEXT'),
                                              ('passfail', 'NUMERIC')])
    assert test_soc_db.schema == OrderedDict([('raw_id', 'TEXT'),
                                              ('text', 'TEXT'),
                                              ('time_zone', 'NUMERIC'),
                                              ('fresh', 'NUMERIC'),
                                              ('date_posted', 'DATE'),
                                              ('post_error', 'NUMERIC')])
    test_close_all()


def test_days_in_history():
    init()
    # Check that random days will return list
    print("Testing days in history")
    for _ in range(5):
        assert isinstance(test_hist_db.get_rows_by_date(random.randint(1, 365)), list)

    # Check the change_date() method works
    # Get five random raw_ids and five random dates
    raw_ids_dict = {}
    for _ in range(5):
        raw_ids_dict[(test_hist_db.all_rows_list()[random.randint(1, (len(test_hist_db.all_rows_list())) - 1)][0])] = \
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
    for k, v in raw_ids_dict.items():
        assert str(k) in str(test_hist_db.get_rows_by_date(v))
    test_close_all()


def test_time_zone():
    init()
    print("Testing SocMediaDB time zones.")
    # Get five random raw_ids
    raw_ids_dict = {}
    for _ in range(5):
        random_zone = random.randint(-10, 12)
        if len(test_soc_db.get_rows_by_time_zone(time_zone=random_zone)) > 0:
            random_index = random.randint(1, len(test_soc_db.get_rows_by_time_zone(time_zone=random_zone)) - 1)
        else:
            random_zone = 99
            random_index = random.randint(1, len(test_soc_db.get_rows_by_time_zone(time_zone=random_zone)) - 1)
        assert isinstance(test_soc_db.get_rows_by_time_zone(time_zone=random_zone), list)
        raw_ids_dict[(test_soc_db.get_rows_by_time_zone(time_zone=random_zone)[random_index][0])] = random_zone

    # Change time zones for five random raw_ids
    for k, v in raw_ids_dict.items():
        test_soc_db.change_time_zone(raw_id=k, new_zone=v)
    # Re-initialize database and make sure row counts match
    test_close_all()
    init()
    test_row_count()
    # Check that the five raw_ids have the new random dates
    init()
    for k, v in raw_ids_dict.items():
        assert str(k) in str(test_soc_db.get_rows_by_time_zone(v))
    test_close_all()
    init()


def test_update_to_not_fresh():
    init()
    print("Testing update to not fresh")
    # Testing SocDB method for making not fresh
    my_list = []
    for _ in range(5):
        random_index = random.randint(1, (len(test_soc_db.all_rows_list()) - 1))
        my_list.append(test_soc_db.all_rows_list()[random_index][0])
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
            if j[0] == i:
                assert j[3] == 0
    test_close_all()


def test_make_fresh_again():
    print("Testing making fresh again")
    init()
    # TODO need to give post_date to all entries or make fresh again will crash
    for i in test_soc_db.all_rows_list():
        test_soc_db.curs.execute("UPDATE {} SET date_posted={} WHERE raw_id='{}'".format('socmediamaps', time.time(), i[0]))
    test_soc_db.make_fresh_again(current_time=9999999999)
    init()
    test_row_count()
    init()
    assert test_soc_db.fresh_count == test_soc_db.rows_count
    test_close_all()


def test_last_24_hour_methods():
    print("Testing previous 24 hour methods")
    init()
    assert isinstance(test_log_db.get_fails_previous_24(current_time=time.time()), list)
    assert isinstance(test_log_db.get_successes_previous_24(current_time=time.time()), list)
    test_close_all()


def test_add_entries(num_of_entries):
    # Add random new entries to database
    init()
    print("Adding {} random entries to all databases for testing...".format(
        str(num_of_entries)
    ))
    for _ in range(num_of_entries):
        rand_hist_id = create_random_string(6)
        rand_soc_id = create_random_string(6)
        rand_log_text = create_random_string(11)
        rand_passfail = random.randint(0, 1)
        test_hist_db.add_row_to_db(raw_id=rand_hist_id,
                                   text=create_random_string(10),
                                   day_of_year=random.randint(1, 365))
        my_diag_dic = Diagnostic(script=(create_random_string(8)) + '.py')
        my_diag_dic.raw_id = create_random_string(6)
        my_diag_dic.severity = random.randint(1, 9)
        my_diag_dic.table = create_random_string(6)
        my_diag_dic.traceback = create_random_string(15)
        my_diag_dic.tweet = "http://" + str(create_random_string(8))
        test_log_db.add_row_to_db(diagnostics=my_diag_dic.make_dict(),
                                  error_text=rand_log_text,
                                  passfail=rand_passfail)
        init()
        test_soc_db.add_row_to_db(raw_id=rand_soc_id,
                                  text=create_random_string(11),
                                  time_zone=random.randint(-10, 12),
                                  fresh=random.randint(0, 1))
        test_close_all()
        init()
        if rand_passfail == 0:
            assert rand_log_text in str(test_log_db.get_fails_previous_24(current_time=time.time()))
            # TODO make a better assertion for checking diagnositcs in previous 24 hours
            assert my_diag_dic.raw_id in str(test_log_db.get_fails_previous_24(current_time=time.time()))
        elif rand_passfail == 1:
            assert rand_log_text in str(test_log_db.get_successes_previous_24(current_time=time.time()))
            assert my_diag_dic.raw_id in str(test_log_db.get_successes_previous_24(current_time=time.time()))
    test_close_all()
    init()
    test_row_count(delta=num_of_entries)


def main_test_db(num_of_entries=5):
    t_start = time.perf_counter()
    init()
    # Get count of all rows of each database
    test_hist_db_old_count = test_hist_db.rows_count
    test_log_db_old_count = test_log_db.rows_count
    test_soc_db_old_count = test_soc_db.rows_count
    test_check_integrity()
    test_row_count()
    test_schema()
    test_days_in_history()
    test_time_zone()
    test_update_to_not_fresh()
    test_make_fresh_again()
    test_last_24_hour_methods()

    test_add_entries(num_of_entries=num_of_entries)
    print("Checking DB integrity again.")
    test_check_integrity()
    print("Tests Passed, deleting test database")
    os.remove(test_db_path)
    t_stop = time.perf_counter()
    print(t_stop-t_start)
    return t_stop - t_start


init()
test_hist_db_old_count = test_hist_db.rows_count
test_log_db_old_count = test_log_db.rows_count
test_soc_db_old_count = test_soc_db.rows_count

if __name__ == "__main__":
    main_test_db(5)