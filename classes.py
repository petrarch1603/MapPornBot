import ast
from collections import OrderedDict
import csv
import facebook
import functions
import os
import praw
import random
import requests
from secrets import *
from secret_tumblr import *
from shutil import copyfile
import sqlite3
import time
import tweepy


class MapRow():
    """
    Class for turning a map row into an object.

    Attributes:
        schema (dict): The database schema
        row (list): List of all the elements of a single database row instance
    """

    def __init__(self, schema, row, table):
        """
        The constructor for MapRow class.

        :param schema: (dict) keys of schema are the names of the each schema element
        :param row: (list) list of all elements of a single database row instance
        """
        self.schema = schema.keys()
        if len(row) != len(self.schema):
            raise ValueError("schema size and row size must be equal")
        self.dict = dict(zip(self.schema, row))
        self.table = table
        self.text = ''
        self.announce_input = ''
        # Set attributes from keys of row dictionary
        for k, v in self.dict.items():
            self.__dict__[str(k)] = v
        r = praw.Reddit('bot1')
        self.praw = r.submission(id=self.dict['raw_id'])
        self.diag = None

    def date(self):
        """
        The function to get a date in a human readable format

        :return: date in human readable format
        """
        try:
            self.dict['day_of_year']
        except KeyError:
            print("No information for day_of_year")
            return
        import datetime
        dt = datetime.datetime(2010, 1, 1)
        dtdelta = datetime.timedelta(days=self.dict['day_of_year'])
        return (dt + dtdelta).strftime('%Y/%m/%d')

    def create_diagnostic(self, script): # Note do not run this from the script, use post_to_social_media() instead
        map_row_diag = Diagnostic(script=script)
        for k, v in self.dict.items():
            if k == 'raw_id':
                map_row_diag.raw_id = v
            if k == 'text':
                map_row_diag.title = v
            if k == 'time_zone':
                map_row_diag.zone = int(v)
        self.diag = map_row_diag

    def blast(self):  # Note do not run this from the script, use post_to_social_media() instead
        try:
            my_blast = ShotgunBlast(praw_obj=self.praw, title=self.text, announce_input=self.announce_input)
            assert my_blast.check_integrity() == 'PASS'
            s_b_dict = my_blast.post_to_all_social()
            self.diag.tweet = s_b_dict['tweet_url']
            self.diag.add_to_logging(passfail=1)
        except AssertionError as e:
            functions.send_reddit_message_to_self(
                title='error',
                message="shotgun blast intergirty check failed!   \n"
                        "{}".format(str(e)))
            self.diag.severity = 2
            self.diag.traceback = e
            self.diag.add_to_logging(passfail=0)
        except tweepy.TweepError as e:
            functions.send_reddit_message_to_self(
                title='tweepy error',
                message='Error doing maprow blast:   \n{}'.format(e))
            self.diag.severity = 1
            self.diag.traceback = e
            self.diag.add_to_logging(passfail=0)

    def post_to_social_media(self, table, script):
        self.create_diagnostic(script=script)
        self.diag.table = table
        self.blast()


class Diagnostic:
    """This is a class for diagnosing failures and success of scripts."""

    def __init__(self, script, path='data/mapporn.db', **kwargs):
        """
        The constructor for Diagnostic class.
        :param script: (str) The name of the script. This param is mandatory.
        :param kwargs: The other arguments are optional, default is None.
        :param raw_id: (str) six character raw id of target Reddit source
        :param severity: (int) arbitrary number to indicate severity of failure.
        :param table: (str) Database table name.
        :param traceback: (str) Traceback of error message.
        :param title: (str) Title.
        :param zone: (int) Time zone.
        :param path: (str) Path to database, defaults to production database, can be changed for testing.
        """
        self.raw_id = None
        self.severity = None
        self.table = None
        self.traceback = None
        self.tweet = None
        self.title = None
        self.zone = None
        self.script = script
        self.__dict__.update(kwargs)
        self.path = path

    @classmethod
    def diag_dict_to_obj(cls, diag_dict):
        """
        Class Method for taking a dictionary and making it an object.

        :param diag_dict: (dict)
        :return: (obj) returns an instance of Diagnostic classs.
        """
        if type(diag_dict) == str:
            diag_dict = ast.literal_eval(diag_dict)
        my_diag = Diagnostic(script=diag_dict['script'])
        for k, v in diag_dict.items():
            if k == 'raw_id':
                my_diag.raw_id = v
            elif k == 'severity':
                my_diag.severity = v
            elif k == 'table':
                my_diag.table = v
            elif k == 'traceback':
                my_diag.traceback = v
            elif k == 'tweet':
                my_diag.tweet = v
            elif k == 'title':
                my_diag.title = v
            elif k == 'zone':
                my_diag.zone = v
        return my_diag

    def make_dict(self):
        """
        Makes a dictionary from a Diagnostic object.

        :return: (dict) of all object attributes.
        """
        try:
            if self.raw_id is not None:
                assert self.title is not None
        except AssertionError:
                functions.send_reddit_message_to_self(title="Missing title",
                                                      message="{} script is missing a title. When you pass in a raw_id "
                                                              "there should be a title too.".format(self.script))
        return {
            "raw_id": self.raw_id,
            "script": self.script,
            "severity": int(self.severity),
            "table": self.table,
            "traceback": str(self.traceback),
            "tweet": str(self.tweet),
            "title": str(self.title),
            "zone": self.zone
        }

    def concise_diag(self):
        """
        Returns a pretty string of the contents of the Diagnostic object without any blank attributes.

        :return: (str) Pretty string for seeing the contents of the Diagnostic object.
        """
        # TODO need to add testing on this method
        # This method prunes out any blank/null/empty fields and returns string of contents
        if self.traceback == 'No New Mail':
            return '***\n    \n'
        else:
            my_string = "Script: {}   \n".format(str(self.script))
            my_string += "Raw_id: {}   \n".format(str(self.raw_id)) if self.raw_id is not None else ''
            my_string += "Title: {}    \n".format(str(self.title)) if self.title is not None else ''
            my_string += "Table: {}    \n".format(str(self.table)) if self.table is not None else ''
            my_string += "Traceback: {}    \n".format(str(self.traceback)) if self.traceback is not None else ''
            my_string += "***\n   \n"
            return my_string

    def add_to_logging(self, passfail):
        log_db = LoggingDB(path=self.path)
        log_db.add_row_to_db(diagnostics=self.make_dict(), passfail=passfail)


class MapDB:
    def __init__(self, table, path='data/mapporn.db'):
        self.path = path
        self.table = table
        self.conn = sqlite3.connect(path)
        self.curs = self.conn.cursor()
        self.rows_count = self.curs.execute('SELECT count(*) FROM {}'.format(self.table)).fetchall()[0][0]
        schema_dic = OrderedDict()
        self.curs.execute("PRAGMA TABLE_INFO('{}')".format(self.table))
        for tup in self.curs.fetchall():
            schema_dic[tup[1]] = tup[2]
        self.schema = schema_dic

    def __len__(self):
        return self.curs.execute('SELECT count(*) FROM {}'.format(self.table)).fetchall()[0][0]

    def all_rows_list(self):
        return self.curs.execute("SELECT * FROM {}".format(self.table)).fetchall()

    def get_random_row(self, count=1):
        return self.curs.execute("SELECT * FROM {} ORDER BY RANDOM() LIMIT {}".format(self.table, count)).fetchall()

    def delete_by_raw_id(self, raw_id_to_delete):
        if len(self.curs.execute("SELECT * FROM {} WHERE raw_id = '{}'".format(
                self.table,
                raw_id_to_delete)).fetchall()) == 0:
            return "Raw_id not in database"
        else:
            self.curs.execute("DELETE FROM {} WHERE raw_id = '{}'".format(self.table, raw_id_to_delete))
            try:
                assert len(self.curs.execute("SELECT * FROM {} WHERE raw_id = '{}'".format(
                    self.table,
                    raw_id_to_delete)).fetchall()) == 0
            except AssertionError as e:
                return "Unable to delete raw_id, row still in database. {}".format(e)

    def close(self):
        self.conn.commit()
        self.conn.close()


class HistoryDB(MapDB):
    def __init__(self, table='historymaps', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)

    def get_rows_by_date(self, date):
        assert isinstance(date, int)
        rows_list = [x for x in (self.curs.execute("SELECT * FROM {} WHERE day_of_year = {}".format(self.table, date)))]
        obj_list = []
        if len(rows_list) > 0:
            for i in range(len(rows_list)):
                my_row = MapRow(schema=self.schema, row=rows_list[i], table=self.table)
                obj_list.append(my_row)
        return obj_list

    def change_date(self, raw_id, new_date):
        self.curs.execute("UPDATE {} SET day_of_year={} WHERE raw_id='{}'".format(self.table, new_date, raw_id))
        self.conn.commit()

    def add_row_to_db(self, raw_id, text, day_of_year):
        self.curs.execute('''INSERT INTO {table} values("{raw_id}", "{text}", {day_of_year})'''
                          .format(table=self.table,
                                  raw_id=raw_id,
                                  text=text,
                                  day_of_year=day_of_year))
        self.conn.commit()

    def check_integrity(self):
        status = ''
        for i in self.all_rows_list():
            try:
                assert isinstance(i[2], int) and (0 < i[2] < 366), "Dates must be between 1 and 365"
            except AssertionError as e:
                status += "* Not all day_of_year in {} are valid days\n  {}\n  {}\n\n"\
                    .format(self.table, str(i), e)
            try:
                assert i[1] != ''
            except AssertionError as e:
                status += "* Title of {} is blank in {}\n  {}\n\n".format(
                    i[0], self.table, e
                )
            try:
                assert len(i[0]) == 6
            except AssertionError as e:
                status += "* raw_id of {} in {} is not acceptable\n  {}\n\n".format(
                    i[0], self.table, e
                )
        for _ in range(5):
            try:
                assert isinstance(self.get_rows_by_date(random.randint(1, 365)), list)
            except AssertionError as e:
                status += "* Randoms days do not return a list   \n{}    \n{}   \n".format(str(e), str(type(e)))
        try:
            assert self.schema == OrderedDict([('raw_id', 'TEXT'),
                                               ('text', 'TEXT'),
                                               ('day_of_year', 'NUMERIC')])
        except AssertionError as e:
            status += "* Schema check failed!   \n{}    \n{}   \n".format(str(e), str(type(e)))
        if status == '':
            return 'PASS: {} integrity test passed.'.format(self.table)
        else:
            return status

    def get_row_by_raw_id(self, raw_id):
        my_row = self.curs.execute("""SELECT * FROM {} WHERE raw_id='{}'""".format(
            self.table,
            raw_id
            )).fetchall()
        if len(my_row) == 1:
            return my_row[0]
        else:
            return my_row


class SocMediaDB(MapDB):
    def __init__(self, table='socmediamaps', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)
        self.fresh_count = self.curs.execute("SELECT count(*) FROM {} WHERE fresh=1"
                                             .format(self.table)).fetchall()[0][0]
        zone_dict = {
            "n_america": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (-9,-8,-7,-6,-5) AND fresh = 1"
                                           .format(self.table)).fetchone()[0],
            "s_america": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (-5,-4,-3) AND fresh = 1"
                                           .format(self.table)).fetchone()[0],
            "w_europe": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (0,1) AND fresh = 1"
                                          .format(self.table)).fetchone()[0],
            "e_europe": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (2,3) AND fresh = 1"
                                          .format(self.table)).fetchone()[0],
            "c_asia": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (4,5,6) AND fresh = 1"
                                        .format(self.table)).fetchone()[0],
            "e_asia": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (7,8,9) AND fresh = 1"
                                        .format(self.table)).fetchone()[0],
            "oceania": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (10,11,12,-10) AND fresh = 1"
                                         .format(self.table)).fetchone()[0],
            "no_zone": self.curs.execute("SELECT count(*) FROM {} WHERE time_zone in (99) AND fresh = 1"
                                         .format(self.table)).fetchone()[0]
        }
        self.zone_dict = zone_dict
        self.not_fresh_list = self.curs.execute("SELECT * FROM {} WHERE fresh=0".format(self.table)).fetchall()

    @classmethod
    def get_time_zone(cls, title_str):
        with open('data/locationsZone.csv', 'r') as f:
            csv_reader = csv.reader(f)
            zonedict = {rows[0].upper(): rows[1] for rows in csv_reader}
        this_zone = 99
        for place in zonedict:
            if place in functions.strip_punc(title_str.upper()):
                this_zone = int(zonedict[place])
        return this_zone

    def get_rows_by_time_zone(self, time_zone, fresh=1):
        if isinstance(time_zone, int):
            return [x for x in (self.curs.execute("SELECT * FROM {} WHERE time_zone = {} AND fresh = {}"
                                                  .format(self.table, time_zone, fresh)))]
        elif isinstance(time_zone, list):
            time_zone_list = []
            for i in time_zone:
                for j in self.curs.execute("SELECT * FROM {} WHERE fresh={} and time_zone={}"
                                           .format(self.table, fresh, i)):
                    time_zone_list.append(j)
            return time_zone_list
        else:
            print(str(time_zone) + " is not a valid time zone")

    def change_time_zone(self, raw_id, new_zone):
        self.curs.execute("UPDATE {} SET time_zone = {} WHERE raw_id = '{}'".format(
            self.table,
            new_zone,
            raw_id))
        self.conn.commit()

    def update_to_not_fresh(self, raw_id):
        self.curs.execute("UPDATE {} SET fresh=0 WHERE raw_id='{}'".format(self.table, raw_id))
        self.curs.execute("UPDATE {} SET date_posted={} WHERE raw_id='{}'"
                          .format(self.table, (int(time.time())), raw_id))
        self.conn.commit()

    def get_one_map_row(self, target_zone):
        min_target = (int(target_zone) - 3)
        max_target = (int(target_zone) + 3)
        filtered_map_list = list(row for row in self.curs.execute(
            "SELECT * FROM {} WHERE fresh=1 AND time_zone >= {} AND time_zone <= {}"
            .format(self.table, min_target, max_target)
        ))
        if len(filtered_map_list) == 0:
            filtered_map_list = list(row for row in self.curs.execute(
                "SELECT * FROM {} WHERE fresh=1 AND time_zone = 99"
                .format(self.table)
            ))
        if len(filtered_map_list) == 0:
            filtered_map_list = list(row for row in self.curs.execute(
                "SELECT * FROM {} WHERE fresh=1 AND time_zone = {}".format(
                    self.table,
                    # Sort the time zones and return the time_zone with the highest count of fresh maps
                    sorted(self.zone_dict.items(), key=lambda x: x[1], reverse=True)[0][1])
            ))
        if len(filtered_map_list) == 0:
            return print("No fresh maps in database!")
        my_row = random.choice(filtered_map_list)
        return MapRow(schema=self.schema, row=my_row, table=self.table)

    def add_row_to_db(self, raw_id, text, time_zone, fresh=1, date_posted='NULL', post_error=0):
        self.curs.execute('''INSERT INTO {table} values('{raw_id}', 
                          "{text}", {time_zone}, {fresh}, {date_posted}, {post_error})'''
                          .format(table=self.table,
                                  raw_id=raw_id,
                                  text=text,
                                  time_zone=time_zone,
                                  fresh=int(fresh),
                                  date_posted=date_posted,
                                  post_error=int(post_error)))
        self.conn.commit()

    def check_if_already_in_db(self, raw_id):
        if len(self.curs.execute("SELECT * FROM {} WHERE raw_id = '{}'".format(self.table, raw_id)).fetchall()) >= 1:
            return True
        else:
            return False

    def check_integrity(self):
        status = ''
        for i in self.all_rows_list():
            try:
                assert i[1] != ''
            except AssertionError as e:
                status += "* Title of {} is blank in {}     \n{}    \n{}    \n".format(
                    str(i[0]), str(self.table), str(e), str(type(e))
                )
            try:
                assert 4 < len(i[0]) < 7
            except AssertionError as e:
                status += "* raw_id of {} in {} is not acceptable    \n{}     \n{}    \n".format(
                    str(i[0]), str(self.table), str(e), str(type(e))
                )
            try:
                assert (-10 <= int(i[2]) <= 12) or int(i[2]) == 99
            except AssertionError as e:
                status += "* time_zone of {} in {} is not acceptable    \n{}    \n{}   \n".format(
                    str(i[0]), str(self.table), str(e), str(type(e))
                )
            try:
                assert (int(i[3]) == 0) or (int(i[3]) == 1)
            except AssertionError as e:
                status += "* fresh of {} is not a boolean in {}   \n{}    \n{}    \n".format(
                    str(i[0]), str(self.table), str(e), str(type(e))
                )
            try:
                if int(i[3]) == 0:
                    assert len(str(i[4])) >= 10
            except AssertionError as e:
                status += "* Item {} is not fresh and does not have a date_posted date    \n{}    \n{}    \n".format(
                    str(i[0]), str(e), str(type(e))
                )

            # Is the following code necessary? Sometimes older posts will stay not-fresh until they are refreshed.
            try:
                if i[3] == 0:
                    assert int(i[4]) >= (time.time() - 37500000)
            except AssertionError as e:
                status += "* Item {} has a date_posted older than a year.   \n{}    \n{}   \n".format(
                    str(i), str(e), str(type(e))
                )
            try:
                assert self.check_if_already_in_db(raw_id=i[0]) is True
            except AssertionError as e:
                status += "* Check if already in db method failed.    \n" \
                          "Raw_id{}    \n{}   \n{}    \n".format(str(i), str(e), str(type(e)))
            try:
                assert self.check_if_already_in_db(raw_id='PATRIC') is False
            except AssertionError as e:
                status += "* Check if already in db method failed using a fake raw_id    \n" \
                          "{}    \n{}    \n".format(str(e), str(type(e)))
        try:
            assert self.schema == OrderedDict([('raw_id', 'TEXT'),
                                               ('text', 'TEXT'),
                                               ('time_zone', 'NUMERIC'),
                                               ('fresh', 'NUMERIC'),
                                               ('date_posted', 'DATE'),
                                               ('post_error', 'NUMERIC')])
        except AssertionError as e:
            status += "* Schema check failed!   \n{}    \n{}    \n".format(str(e), str(type(e)))
        try:
            assert len(self.get_duplicates()) == 0
        except AssertionError as e:
            status += "* Duplicates detected!    \n{}    \n".format(str(e))

        try:
            my_random_raw_ids = self.get_random_row(count=5)
            for i in my_random_raw_ids:
                assert self.check_if_already_in_db(raw_id=i[0]) is True
        except AssertionError as e:
            status += "Failure detecting duplicates in database!\n   \n{}".format(str(e))
        if status == '':
            return 'PASS: {} integrity test passed.'.format(self.table)
        else:
            return status

    def make_fresh_again(self, current_time, limit=10):
        assert len(str(int(current_time))) == 10
        default_time_past = 43200000
        # Code below here will increase the amount of time to make fresh when the number of maps in the database is over
        # 4000. My objective is to take a long time before making the maps fresh again.
        time_past = max(int((len(self)/8)*24*59*60), default_time_past)
        cutoff_time = (current_time - int(time_past))
        count = 0
        for i in self.not_fresh_list:
            if int(i[4]) <= cutoff_time:
                if i[2] == 99:
                    new_time_zone = self.get_time_zone(i[1])
                    if new_time_zone != 99:
                        self.curs.execute("UPDATE {} SET time_zone={} WHERE raw_id='{}'".format(self.table,
                                                                                                new_time_zone,
                                                                                                i[0]))
                self.curs.execute("UPDATE {} SET fresh=1 WHERE raw_id='{}'".format(self.table,
                                                                                   i[0]))
                self.conn.commit()
                count += 1
                if count >= limit:
                    self.conn.close()
                    break
        self.conn.close()

    def get_row_by_raw_id(self, raw_id):
        my_row = self.curs.execute("""SELECT * FROM {} WHERE raw_id='{}'""".format(
            self.table,
            raw_id
            )).fetchall()
        if len(my_row) == 1:
            return my_row[0]
        else:
            return my_row

    def get_duplicates(self):
        return self.curs.execute("""SELECT raw_id, count(*) FROM {} GROUP BY raw_id HAVING count(*) > 1""".format(
            self.table)).fetchall()

    def remove_duplicates(self):
        source_db_path = 'data/mapporn.db'
        test_db_path = 'data/test.db'
        copyfile(source_db_path, test_db_path)

        soc_db = SocMediaDB(path=test_db_path)
        duplicates_count = len(soc_db.get_duplicates())
        old_row_count = len(soc_db)

        # Get random rows to check that they are not changed
        random_rows = soc_db.get_random_row(50)

        # Create temporary table
        soc_db.curs.execute('CREATE TEMPORARY TABLE to_delete (raw_id TEXT not null, text TEXT, time_zone NUMERIC, '
                            'fresh NUMERIC, date_posted DATE, post_error NUMERIC, min_id NOT null)').fetchall()

        # Add duplicates to temporary table
        soc_db.curs.execute(
            'INSERT INTO to_delete(raw_id, text, time_zone, fresh, date_posted, post_error, min_id) SELECT raw_id, '
            'text, time_zone, fresh, date_posted, post_error, MIN(rowid) from {} '
            'GROUP BY raw_id HAVING count(*) > 1'.format(self.table)).fetchall()

        # Delete from main table
        soc_db.curs.execute(
            'DELETE FROM socmediamaps WHERE EXISTS(SELECT * FROM to_delete WHERE '
            'to_delete.raw_id = socmediamaps.raw_id AND to_delete.min_id <> socmediamaps.rowid)').fetchall()
        soc_db.conn.commit()

        # Check that the remaining rows are still the same
        assert len(soc_db.get_duplicates()) == 0
        assert len(soc_db) == (old_row_count - duplicates_count)
        for i in random_rows:
            raw_id = i[0]
            db_row = soc_db.curs.execute(
                'SELECT * FROM {} WHERE raw_id = "{}"'.format(self.table, raw_id)).fetchall()
            for j in db_row:
                assert i == j
        copyfile(test_db_path, source_db_path)
        os.remove(test_db_path)


class LoggingDB(MapDB):
    def __init__(self, table='logging', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)

    def add_row_to_db(self, diagnostics, passfail, error_text=None):
        my_sql = '''INSERT INTO logging (date, error_text, diagnostics, passfail) VALUES (?, ?, ?, ?)'''
        my_list = [int(time.time()), str(error_text), str(diagnostics), passfail]
        self.curs.execute(my_sql, my_list)
        self.conn.commit()

    def get_fails_previous_24(self, current_time):
        current_time = int(current_time)
        assert len(str(current_time)) == 10
        # Note: capturing all fails from a little longer than 24 hours ago
        # to ensure it doesn't miss any fails from previous day's script.
        twenty_four_ago = int(current_time) - 87500
        return list(row for row in self.curs.execute(
            "SELECT * FROM {} WHERE passfail = 0 AND date >= {}"
            .format(self.table, twenty_four_ago)
        ))

    def get_fails_in_window(self, newer_time, older_time):
        newer_time = int(newer_time)
        older_time = int(older_time)
        return list(row for row in self.curs.execute(
            "SELECT * FROM {} WHERE passfail = 0 AND date >= {} AND date <= {}"
            .format(self.table,
                    older_time,
                    newer_time)
        ))

    def get_successes_previous_24(self, current_time):
        current_time = int(current_time)
        assert len(str(current_time)) == 10
        # Note: capturing all fails from a little longer than 24 hours ago
        # to ensure it doesn't miss any fails from previous day's script.
        twenty_four_ago = int(current_time) - 87500
        return list(row for row in self.curs.execute(
            "SELECT * FROM {} WHERE passfail = 1 AND date >= {}"
            .format(self.table, twenty_four_ago)
        ))

    def get_fails_by_script(self, script):
        print("Returning list of all fails from {}".format(script))
        return list(row for row in self.curs.execute(
            "SELECT * WHERE passfail = 0 AND diagnostics LIKE '{}'"
            .format(script)
        ))

    def check_integrity(self):
        status = ''
        try:
            for i in self.all_rows_list():
                assert isinstance(i[0], int)
                assert i[3] == 1 or i[3] == 0
                if i[2] is None:
                    raise AssertionError
                this_diag = Diagnostic.diag_dict_to_obj(i[2])
                assert str(this_diag.script).endswith(".py")
                assert self.schema == OrderedDict([('date', 'NUMERIC'),
                                                   ('error_text', 'TEXT'),
                                                   ('diagnostics', 'TEXT'),
                                                   ('passfail', 'NUMERIC')])
        except AssertionError as e:
            status += 'Error encountered: {}\n'.format(str(e))
        try:
            assert isinstance(self.get_fails_previous_24(current_time=time.time()), list)
            assert isinstance(self.get_successes_previous_24(current_time=time.time()), list)
        except AssertionError as e:
            status += '* previous 24 methods did not return lists.\n    {}\n\n'.format(str(e))
        if status == '':
            return "PASS: LoggingDB integrity test passed."
        else:
            print(status)
            return status


class JournalDB(MapDB):
    def __init__(self, table='journal', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)

    def update_todays_status(self, benchmark_time):
        # TODO: verify this is working after errors start getting added to my_dict
        # right now I don't know if the my_dict is working.
        date = time.time()
        hist_db = HistoryDB()
        log_db = LoggingDB()
        soc_db = SocMediaDB()
        # TODO: do i need these three lines for massaging my_dict??
        my_dict = {i[0]: str(i[1:]).replace('"', "\\'") for i in log_db.get_fails_previous_24(date)}
        my_dict = str(my_dict)
        my_dict = my_dict.replace('"', '\'')
        query = """INSERT INTO {table} values(?, ?, ?, ?, ?, ?, ?, ?, ?)""".format(table=self.table)
        self.curs.execute(query, (date,
                                  len(hist_db),
                                  len(log_db),
                                  len(soc_db),
                                  soc_db.fresh_count,
                                  len(log_db.get_fails_previous_24(date)),
                                  len(log_db.get_successes_previous_24(date)),
                                  benchmark_time,
                                  str(my_dict)))
        self.conn.commit()

    def check_integrity(self):
        status = ''
        try:
            for i in self.all_rows_list():
                assert isinstance(i[0], (int, float))
                assert isinstance(i[1], int)
                assert isinstance(i[2], int)
                assert isinstance(i[3], int)
                assert isinstance(i[4], int)
                assert isinstance(i[7], (int, float))
        except AssertionError as e:
            status += "* column type check failed!\n     {}\n\n".format(str(e))
        try:
            assert self.schema == OrderedDict([('date', 'NUMERIC'),
                                              ('hist_rows', 'NUMERIC'),
                                              ('log_rows', 'NUMERIC'),
                                              ('soc_rows', 'NUMERIC'),
                                              ('fresh_rows', 'NUMERIC'),
                                              ('errors_24', 'NUMERIC'),
                                              ('successes_24', 'NUMERIC'),
                                              ('benchmark_time', 'REAL'),
                                              ('dict', 'TEXT')])
        except AssertionError as e:
            status += "* Schema Check Failed!\n     {}\n\n".format(str(e))
        if status == '':
            return "PASS: JournalDB integrity test passed."
        else:
            print(status)
            return status

    def average_benchmark_times(self):
        my_sum = 0
        counter = 0
        for i in self.all_rows_list():
            if i[4] > 0:
                counter += 1
                my_sum += int(i[4])
        return my_sum / counter


class ShotgunBlast:
    def __init__(self, praw_obj, title=None, announce_input=None):
        self.announce_input = announce_input
        self.twitter_max = 280
        self.praw_obj = praw_obj
        self.shortlink = praw_obj.shortlink
        self.title = self.get_title(title)
        self.image_url = self.praw_obj.url
        self.raw_id = self.praw_obj.id

    @classmethod
    def get_hashtag_locations(cls, string):
        my_hashes = ''
        string_list = string.split(' ')
        with open('data/locations.txt') as locationstext:
            locationstext = locationstext.read().split()
            for w in string_list:
                if str(w) in locationstext:
                    my_hashes += '#' + str(w) + ' '
        return my_hashes.rstrip()

    @classmethod
    def remove_text_inside_brackets(cls, text, brackets="[]"):
        count = [0] * (len(brackets) // 2)  # count open/close brackets
        saved_chars = []
        for character in text:
            for i, b in enumerate(brackets):
                if character == b:  # found bracket
                    kind, is_close = divmod(i, 2)
                    count[kind] += (-1) ** is_close  # `+1`: open, `-1`: close
                    if count[kind] < 0:  # unbalanced bracket
                        count[kind] = 0  # keep it
                    else:  # found bracket to remove
                        break
            else:  # character is not a [balanced] bracket
                if not any(count):  # outside brackets
                    saved_chars.append(character)
        return ''.join(saved_chars) \
            .replace("  ", " ") \
            .rstrip() \
            .lstrip()

    @classmethod
    def init_shotgun_blast(cls):
        global api

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        api = tweepy.API(auth)

    def get_title(self, raw_title):
        shortlink = self.shortlink
        working_title = ''
        if self.announce_input is not None:
            working_title = str(self.announce_input) + ' '
        if raw_title is None:
            raw_title = self.praw_obj.title
        working_title = (working_title + ' ' + raw_title).lstrip()
        working_title = self.remove_text_inside_brackets(text=working_title)
        if len(working_title) > self.twitter_max - 26:  # 25 is the length of a reddit short url
            working_title = working_title[:(self.twitter_max - 26)] + '... ' + str(shortlink)
        else:
            if len(working_title) + len(' #MapPorn') + len(shortlink) < self.twitter_max:
                working_title += ' ' + str(shortlink) + ' #MapPorn'
                for w in self.get_hashtag_locations(working_title).split(' '):
                    if (len(working_title) + len('#')) <= self.twitter_max:
                        working_title = working_title.replace((w[1:]), w)
            else:
                working_title += ' ' + str(shortlink)
        assert len(working_title) <= self.twitter_max
        return working_title

    def download_image(self):
        filename = 'temp.jpg'
        request = requests.get(self.image_url, stream=True)
        try:
            if request.status_code == 200:
                with open(filename, 'wb') as image:
                    for chunk in request:
                        image.write(chunk)
                filesize = os.path.getsize('temp.jpg')
            else:
                url = self.praw_obj.preview['images'][0]['resolutions'][3][
                    'url']  # This is the smaller image. Using this because Twitter doesn't like huge files.
                request = requests.get(url, stream=True)
                try:
                    assert request.status_code == 200
                    with open(filename, 'wb') as image:
                        for chunk in request:
                            image.write(chunk)
                    filesize = os.path.getsize('temp.jpg')
                except AssertionError as e:
                    raise Exception('Could not download image! Reddit might be down.    \n{}    \n\n'.format(str(e)))
            if filesize > 3070000:
                os.remove(filename)
                filename = 'temp.jpg'
                url = self.praw_obj.preview['images'][0]['resolutions'][3][
                    'url']  # This is the smaller image. Using this because Twitter doesn't like huge files.
                request = requests.get(url, stream=True)
                try:
                    assert request.status_code == 200
                    with open(filename, 'wb') as image:
                        for chunk in request:
                            image.write(chunk)
                except AssertionError as e:
                    raise Exception('Could not download image! Reddit might be down.    \n{}    \n\n'.format(str(e)))
            return filename
        except AssertionError as e:
            raise Exception('Could not download image!    \n{}    \n\n'.format(str(e)))

    def post_to_all_social(self):
        self.init_shotgun_blast()
        filename = self.download_image()

        # Post to Twitter
        tweeted = api.update_with_media(filename, status=self.title)  # Post to Twitter
        tweet_id = str(tweeted._json['id'])  # This took way too long to figure out.

        # Post to Tumblr
        tumbld = client.create_photo('mappornofficial',
                                     state="published",
                                     tags=['#mapporn'],  # Post to Tumblr
                                     caption=self.title + ' ' + self.image_url,
                                     source=self.shortlink)
        try:
            tumbld_url = tumbld['id']
            tumbld_url = ('http://mappornofficial.tumblr.com/post/' + str(tumbld_url))
        except Exception as e:
            tumbld_url = "Error encountered: {}   \n{}   \n\n".format(str(e), str(type(e)))
        # Post to Facebook

        rq = requests.get(
            'https://graph.facebook.com/v2.11/me/accounts?access_token=EAAB5zddLiesBABHZB9iOgZAmuuapdSvLvfmwB2jkDvxjFyS'
            'OOXeMdRDozYkAZAaxMNGUT8EMNZABtIgTmC8tDgIzYoleEAK5g7EN8k73YdD80Ic1FPUTp3NZBkofGYgzM802KNA3JenjYRUGJ27vKQTV2'
            'RF1ZB3fGNSUNxs1bMwwZDZD%27')
        stuff = rq.json()
        bloody_access_token = (stuff['data'][0]['access_token'])
        graph = facebook.GraphAPI(access_token=bloody_access_token)
        faced = graph.put_photo(image=open(filename, 'rb').read(), message=self.title)
        fb_post_id = faced['post_id']
        fb_post_id = fb_post_id.replace('_', '/')
        fb_url = str('https://www.facebook.com/OfficialMapPorn/photos/rpp.' + str(fb_post_id))

        tweet_url = ('https://twitter.com/MapPornTweet/status/' + tweet_id)
        socialmediadict = {
            "tweet_url": tweet_url,
            "tumblr_url": tumbld_url,
            "facebook_url": fb_url,
            "title": self.title}
        os.remove(filename)
        return socialmediadict

    def check_integrity(self):
        status = ''
        long_lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis turpis ante, eget " \
                     "pellentesque tellus sagittis sed. Nullam vel finibus metus. Aenean bibendum, nisl nec varius " \
                     "ultrices, augue arcu rutrum nunc, vel pharetra justo lorem vel leo. Aenean ut varius justo. " \
                     "Nunc non dui rutrum, commodo magna a posuere."
        try:
            assert len(self.raw_id) == 6
        except AssertionError as e:
            status += 'raw_id not length 6!    \n{}    \n\n'.format(str(e))

        # Test Bracket Removal
        try:
            assert (self.remove_text_inside_brackets("[123] Happy [123] Birthday")) == "Happy Birthday"
            assert (self.remove_text_inside_brackets("[123][123]Happy    ")) == "Happy"
            assert (self.remove_text_inside_brackets("[OC][123]My Map   ")) == "My Map"
        except AssertionError as e:
            status += 'Remove text inside bracket test FAILED    \n{}    \n\n'.format(str(e))

        # Test get_hashtag_locations
        try:
            assert (self.get_hashtag_locations('England London capital city') == '#England #London')
            assert (self.get_hashtag_locations('Germany is in Europe') == '#Germany #Europe')
            assert (self.get_hashtag_locations('My Map is here') == '')
            assert (self.get_hashtag_locations('USA is great []123297ofhdsd[][]#') == '#USA')
            if self.announce_input is None:
                assert (self.get_title(raw_title="England [123]") == '#England ' +
                        str(self.praw_obj.shortlink) + ' #MapPorn')
        except AssertionError as e:
            status += 'Hashtag_locations test FAILED    \n{}    \n\n'.format(str(e))

        # Test Edge cases
        try:
            # Test title input of 320 chars
            # TODO: add tests for variable announce_input lengths
            if self.announce_input is None:
                assert (self.get_title(raw_title=long_lorem)) == \
                       'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis turpis ante, ' \
                       'eget pellentesque tellus sagittis sed. Nullam vel finibus metus. Aenean bibendum, nisl nec ' \
                       'varius ultrices, augue arcu rutrum nunc, vel pharetra justo lorem vel leo. Aen... ' + \
                       str(self.shortlink)
            # Test title length of 270
                assert (self.get_title(raw_title='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque nec '
                                                 'magna luctus, vestibulum diam sed, condimentum ante. Sed pharetra '
                                                 'blandit tortor, non tempus ex suscipit vel. Nulla facilisi. Quisque orci '
                                                 'est, aliquam in ornare ac, scelerisque quis dui. Nullam metus.')) \
                    == 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque nec magna luctus, vestibulum ' \
                       'diam sed, condimentum ante. Sed pharetra blandit tortor, non tempus ex suscipit vel. Nulla ' \
                       'facilisi. Quisque orci est, aliquam in ornare ac, scelerisque quis du... ' + self.shortlink
            # Test title input of length 245 (280 - shortlink length). Should include #MapPorn
                assert (self.get_title(raw_title='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis '
                                                 'turpis ante, eget pellentesque Quebec sagittis sed. Nullam vel finibus '
                                                 'metus. Aenean bibendum, nisl nec varius ultrices, augue arcu rutrum '
                                                 'nunc, vel pharetra justo lorem vel yz')) \
                    == 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis turpis ante, eget ' \
                       'pellentesque Quebec sagittis sed. Nullam vel finibus metus. Aenean bibendum, nisl nec varius ' \
                       'ultrices, augue arcu rutrum nunc, vel pharetra justo lorem vel yz ' + self.shortlink + ' #MapPorn'
            # Test title input with location hashtag
                assert (self.get_title(raw_title='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis '
                                                 'turpis ante, eget pellentesque tellus sagittis sed. Nullam vel finibus '
                                                 'metus. Aenean bibendum, nisl nec varius ultrices, augue arcu rutrum '
                                                 'nunc, vel pharetra justo lore London')) \
                    == 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis turpis ante, eget ' \
                       'pellentesque tellus sagittis sed. Nullam vel finibus metus. Aenean bibendum, nisl nec varius ' \
                       'ultrices, augue arcu rutrum nunc, vel pharetra justo lore #London ' + self.shortlink + ' #MapPorn'
        except AssertionError as e:
            status += 'get_title test FAILED    \n{}    \n\n'.format(str(e))
            print(status)
            return status

        if status == '':
            status = "PASS"
        else:
            print(status)
        return status


class GenericPost:
    def __init__(self, filename, title):
        self.filename = filename
        self.title = title

    def post_to_all_social(self):
        ShotgunBlast.init_shotgun_blast()
        # Post to Twitter
        tweeted = api.update_with_media(self.filename, status=self.title)  # Post to Twitter
        tweet_id = str(tweeted._json['id'])  # This took way too long to figure out.

        # Post to Tumblr
        tumbld = client.create_photo('mappornofficial',
                                     state="published",
                                     tags=['#mapporn'],  # Post to Tumblr
                                     caption=self.title,
                                     source="http://mapporn.org")
        try:
            tumbld_url = tumbld['id']
            tumbld_url = ('http://mappornofficial.tumblr.com/post/' + str(tumbld_url))
        except Exception as e:
            tumbld_url = "Error encountered: {}   \n{}    \n".format(str(e), str(type(e)))

        # Post to Facebook
        rq = requests.get(
            'https://graph.facebook.com/v2.11/me/accounts?access_token=EAAB5zddLiesBABHZB9iOgZAmuuapdSvLvfmwB2jkDvxjFyS'
            'OOXeMdRDozYkAZAaxMNGUT8EMNZABtIgTmC8tDgIzYoleEAK5g7EN8k73YdD80Ic1FPUTp3NZBkofGYgzM802KNA3JenjYRUGJ27vKQTV2'
            'RF1ZB3fGNSUNxs1bMwwZDZD%27')
        stuff = rq.json()
        bloody_access_token = (stuff['data'][0]['access_token'])
        graph = facebook.GraphAPI(access_token=bloody_access_token)
        faced = graph.put_photo(image=open(self.filename, 'rb').read(), message=self.title)
        fb_post_id = faced['post_id']
        fb_post_id = fb_post_id.replace('_', '/')
        fb_url = str('https://www.facebook.com/OfficialMapPorn/photos/rpp.' + str(fb_post_id))
        tweet_url = ('https://twitter.com/MapPornTweet/status/' + tweet_id)
        socialmediadict = {
            "tweet_url": tweet_url,
            "tumblr_url": tumbld_url,
            "facebook_url": fb_url,
            "title": self.title}
        print(socialmediadict)
        return socialmediadict
