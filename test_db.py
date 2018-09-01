from classes import *
import random
from shutil import copyfile
import string

source_db_path = 'data/mapporn.db'
test_db_path = 'data/test.db'
copyfile(source_db_path, test_db_path)

test_hist_db_old_count = test_hist_db.rows_count
test_log_db_old_count = test_log_db.rows_count
test_soc_db_old_count = test_soc_db.rows_count

# TODO get all the available methods for classes


def init():
    global test_hist_db, test_log_db, test_soc_db
    test_hist_db = HistoryDB(path=test_db_path)
    test_log_db = LoggingDB(path=test_db_path)
    test_soc_db = SocMediaDB(path=test_db_path)


def test_check_integrity():
    print("Checking Database Integrity")
    test_hist_db.check_integrity()
    # TODO check integrity of log DB
    test_soc_db.check_integrity()


def create_random_string(char_count):
    allchar = string.ascii_letters + string.digits
    rand_str = "".join(random.choice(allchar) for _ in range(char_count))
    return rand_str


def test_row_count(delta=0):
    print("Testing Row Count")
    # Delta will be to test for a change. In later functions the database will be changed and this argument is to verify
    # the new count.
    init()
    # Check that row count returns integer
    assert isinstance(test_hist_db.rows_count, int)
    assert isinstance(test_log_db.rows_count, int)
    assert isinstance(test_soc_db.rows_count, int)

    # Check that row count is equal to length of .all_rows_list() method
    assert test_hist_db_old_count + delta == len(test_hist_db.all_rows_list())
    assert test_log_db_old_count + delta == len(test_log_db.all_rows_list())
    assert test_soc_db_old_count + delta == len(test_soc_db.all_rows_list())
    init()


def test_schema():
    print("Testing Schema")
    # Check that the schema is correct
    assert test_hist_db.schema == OrderedDict([('raw_id', 'TEXT'),
                                               ('text', 'TEXT'),
                                               ('day_of_year', 'NUMERIC')])
    # TODO: write test for log_db schema assert test_log_db.schema ==
    assert test_soc_db.schema == OrderedDict([('raw_id', 'TEXT'),
                                              ('text', 'TEXT'),
                                              ('time_zone', 'NUMERIC'),
                                              ('fresh', 'NUMERIC'),
                                              ('date_posted', 'DATE'),
                                              ('post_error', 'NUMERIC')])
    init()


def test_days_in_history():
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
    init()
    test_row_count()

    # Check that the five raw_ids have the new random dates
    for k, v in raw_ids_dict.items():
        assert str(k) in str(test_hist_db.get_rows_by_date(v))
    init()


def test_time_zone():
    print("Testing SocMediaDB time zones.")
    # Get five random raw_ids
    raw_ids_dict = {}
    for _ in range(5):
        random_zone = random.randint(-10, 12)
        random_index = random.randint(1, len(test_soc_db.get_rows_by_time_zone(time_zone=random_zone)))
        assert isinstance(test_soc_db.get_rows_by_time_zone(time_zone=random_zone), list)
        raw_ids_dict[(test_soc_db.get_rows_by_time_zone(time_zone=random_zone)[random_index][0])] = random_zone

    # Change time zones for five random raw_ids
    for k, v in raw_ids_dict.items():
        test_soc_db.change_time_zone(raw_id=k, new_zone=v)
    # Re-initialize database and make sure row counts match
    init()
    test_row_count()
    # Check that the five raw_ids have the new random dates
    for k, v in raw_ids_dict.items():
        assert str(k) in str(test_soc_db.get_rows_by_time_zone(v))
    init()


def test_update_to_not_fresh():
    print("Testing update to not fresh")
    # Testing SocDB method for making not fresh
    my_list = []
    for _ in range(5):
        random_index = random.randint(1, len(test_soc_db.all_rows_list()))
        my_list.append(test_soc_db.all_rows_list()[random_index][0])
    for i in my_list:
        test_soc_db.update_to_not_fresh(raw_id=i)
    # Re-initialize database
    init()
    test_row_count()
    # Check that the five raw_ids are not fresh
    all_rows = test_soc_db.all_rows_list()
    for i in my_list:
        for j in all_rows:
            if j[0] == i:
                assert j[3] == 0
    init()


def test_make_fresh_again():
    print("Testing making fresh again")
    test_soc_db.make_fresh_again(current_time=999999999999)
    init()
    test_row_count()
    assert test_soc_db.fresh_count == test_soc_db.rows_count
    init()

def test_last_24_hour_methods():
    print("Testing previous 24 hour methods")
    assert isinstance(test_log_db.get_fails_previous_24(current_time=time.time()), list)
    assert isinstance(test_log_db.get_successes_previous_24(current_time=time.time()), list)
    init()


def test_add_entries(num_of_entries):
    # Add random new entries to database
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
        my_diag_dic = {}
        for _ in range(3):
            my_diag_dic[create_random_string(5)] = create_random_string(10)
        test_log_db.add_row_to_db(diagnostics=my_diag_dic,
                                  error_text=rand_log_text,
                                  passfail=random.randint(0, 1))
        test_soc_db.add_row_to_db(raw_id=rand_soc_id,
                                  text=create_random_string(11),
                                  time_zone=random.randint(-10, 12),
                                  fresh=random.randint(0, 1))
        init()
        if rand_passfail == 0:
            assert rand_log_text in str(test_log_db.get_fails_previous_24(current_time=time.time()))
        elif rand_passfail == 1:
            assert rand_log_text in str(test_log_db.get_successes_previous_24(current_time=time.time()))

    init()
    test_row_count(delta=num_of_entries)


def main():
    num_of_entries = 5
    init()
    test_check_integrity()
    test_row_count()
    test_schema()
    test_days_in_history()
    test_time_zone()
    test_update_to_not_fresh()
    test_make_fresh_again()
    test_last_24_hour_methods()

    init()
    test_add_entries(num_of_entries=num_of_entries)
    print("Checking DB integrity again.")
    test_check_integrity()
