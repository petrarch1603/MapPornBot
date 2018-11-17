"""Module containing classes for use in MapPorn Reddit Bot

These classes assist in creating several kinds of objects

Classes:
    MapRow - A class that contains the information equivalent to one row of a database. They differ slightly
        depending on which table they are connect.
    Diagnostic - A class that contains diagnostic information for tracking errors and successful execution of scripts.
    MapDB - A super class that connects to a database. Objects are not instantiated with this class, instead they are
        instantiated with subclasses
    HistoryDB - Subclass of MapDB. This class creates an object that can interact with the History database. This
        database contains rows indexed by days of year. The script history.py run every day and will publish a map from
        this row for the corresponding day. This will be published to social media.
    SocMediaDB - Subclass of MapDB. This is a database containing a multitude of maps. Every three hours a map will be
        chosen from this database and published to social media. After the map is published it will be marked as "not
        fresh". After a set amount of time (around 400 days) the map can be "re-freshed". At any given time this
        database will contain a number of 'fresh' maps that are queued up.

        The maps also have a time zone associated with them for publishing at a target time of the day. Every three
        hours the script soc_media_stack.py is run and choses a fresh map to publish to social media.

    LoggingDB - Subclass of MapDB. This is a database of logging data. This database is intended to provide insights
        into script success and failures. Everytime a script is run, a log of data is added to this database.

    JournalDB - Subclass of MapDB. Everyday status.py is ran to test and check functions and methods and to check the
        integrity of the database. The results of this status check are stored in this database.

    ContestDB - Subclass of MapDB. Database for storing map submissions for the monthly contest.

    ShotgunBlast - This class will process data from Reddit and post it to social media.

    GenericPost - This class will post to social media materials that do not come from Reddit.

Attributes:
    schema_dict (dict): Module level dictionary of ordered dictionaries that contain the schema for different databases.
        They are abstracted here to have a common variable that can be accessed from many parts of scripts.

"""

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
from typing import List, Optional, Union


class MapRow:
    """Class for turning a map row into an object.

    Attributes:
        schema (dict): The database schema
        row (list): List of all the elements of a single database row instance

    """

    def __init__(self, schema: dict, row: Union[list, tuple], table: str, path: str = 'data/mapporn.db') -> None:
        """The constructor for MapRow class.

        :param schema: (dict) keys of schema are the names of the each schema element.
        :param row: (list) list of all elements of a single database row instance.
        :param table: (str) name of the database table that this map row belongs to.
        :param path: (str) path

        """
        self.schema = schema.keys()
        self.table = table
        if len(row) != len(self.schema) and table != 'contest':
            raise ValueError("length of elements of schema and length of elements in row must be equal")
        self.dict = dict(zip(self.schema, row))
        self.announce_input = ''
        self.author = ''
        self.date_posted = ''
        self.day_of_year = 0
        self.desc = ''
        self.fresh = ''
        self.map_name = ''
        self.raw_id = ''
        self.text = ''
        self.time_zone = ''
        self.url = ''
        # Set attributes from keys of row dictionary
        for k, v in self.dict.items():
            self.__dict__[str(k)] = v
        self.praw = praw.Reddit('bot1').submission(id=self.dict['raw_id'])
        self.diag = None
        self.path = path

    def date(self) -> Optional[str]:
        """Method to get a date in a human readable format

        :return: (str) date in human readable format

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

    def __create_diagnostic(self, script: object) -> None:
        """Method for creating a diagnostic instance attribute as part of the MapRow object

        Private method, meant to be run from other methods.

        :rtype: None

        """
        map_row_diag = Diagnostic(script=script, path=self.path)
        for k, v in self.dict.items():
            if k == 'raw_id':
                map_row_diag.raw_id = v
            if k == 'text':
                map_row_diag.title = v
            if k == 'time_zone':
                map_row_diag.zone = int(v)
        self.diag = map_row_diag
        self.diag.table = self.table

    def __blast(self) -> None:
        """Method (private) for posting to social media."""
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

    def post_to_social_media(self, script: str) -> None:
        """Method posts the map row to social media

        :param script:
        :type script:

        """
        self.__create_diagnostic(script=script)
        self.make_not_fresh()
        self.__blast()

    def add_row_to_db(self, script: str) -> None:
        """Add this row to the database

        :param script: script as a string, passed in for use in the diagnostic object
        :type script: str

        """
        self.__create_diagnostic(script=script)

        if self.table == 'historymaps':
            hist_db = HistoryDB(path=self.path)
            old_row_count = hist_db.rows_count
            hist_db.add_row_to_db(raw_id=self.raw_id, text=self.text, day_of_year=self.day_of_year)
            hist_db.close()
            hist_db = HistoryDB(path=self.path)
            assert old_row_count + 1 == hist_db.rows_count
            hist_db.close()
        elif self.table == 'socmediamaps':
            soc_db = SocMediaDB(path=self.path)
            assert soc_db.check_if_already_in_db(raw_id=self.raw_id) is False
            old_row_count = soc_db.rows_count
            soc_db.add_row_to_db(raw_id=self.raw_id,
                                 text=self.text,
                                 time_zone=int(self.time_zone),
                                 fresh=int(self.fresh),
                                 date_posted=self.date_posted)
            soc_db.close()
            soc_db = SocMediaDB(path=self.path)
            assert old_row_count + 1 == soc_db.rows_count
            soc_db.close()
        elif self.table == 'contest':
            cont_db = ContestDB(path=self.path)
            assert cont_db.check_if_already_in_db(raw_id=self.raw_id) is False
            old_row_count = cont_db.rows_count
            cont_db.add_to_contest(map_name=self.map_name,
                                   url=self.url,
                                   desc=self.desc,
                                   author=self.author,
                                   raw_id=self.raw_id)
            cont_db.close()
            cont_db = ContestDB(path=self.path)
            assert old_row_count + 1 == cont_db.rows_count
            cont_db.close()
        else:
            self.diag.traceback = "Problem with adding this table: {} to logging database. ".format(self.table)
            self.diag.table = self.table
            self.diag.add_to_logging(passfail=0)
            return
        self.diag.add_to_logging(passfail=1)

    def make_not_fresh(self) -> None:
        """Makes the map row not fresh"""
        assert self.table == 'socmediamaps'
        soc_db = SocMediaDB(path=self.path)
        soc_db.update_to_not_fresh(raw_id=self.raw_id)
        soc_db.close()


class Diagnostic:
    """This is a class for diagnosing failures and success of scripts."""

    def __init__(self, script: object, path: str = 'data/mapporn.db', **kwargs: any) -> None:
        """The constructor for Diagnostic class.

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
        self.severity = 0
        self.table = None
        self.traceback = None
        self.tweet = None
        self.title = None
        self.zone = None
        self.script = script
        self.__dict__.update(kwargs)
        self.path = path

    @classmethod
    def diag_dict_to_obj(cls, diag_dict: dict) -> object:
        """Class Method for taking a dictionary and making it an object.

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

    def make_dict(self) -> dict:
        """Makes a dictionary from a Diagnostic object.

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
            "severity": self.severity,
            "table": self.table,
            "traceback": str(self.traceback),
            "tweet": str(self.tweet),
            "title": str(self.title),
            "zone": self.zone
        }

    def concise_diag(self) -> str:
        """Returns a pretty string of the contents of the Diagnostic object without any blank attributes.

        :return: (str) Pretty string for seeing the contents of the Diagnostic object.

        """

        # TODO need to add testing on this method

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

    def add_to_logging(self, passfail: int) -> None:
        """Add diagnostic object to the logging database.

        :param passfail: 1 for passing, 0 for failure
        :type passfail: int

        """
        log_db = LoggingDB(path=self.path)
        log_db.add_row_to_db(diagnostics=self.make_dict(), passfail=passfail)


class MapDB:
    """This is a super class that makes database objects."""

    def __init__(self, table: str, path: str = 'data/mapporn.db') -> None:
        """ Constructor for the MapDB Class

        :param table: Name of the database table.
        :type table: str
        :param path: Path to database on local disk. Can be changed from default when using a test database.
        :type path: str

        """
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
        assert self.schema == schema_dict[self.table]

    def __len__(self) -> int:
        """Returns the number of records in the database."""
        return self.curs.execute('SELECT count(*) FROM {}'.format(self.table)).fetchall()[0][0]

    def all_rows_list(self) -> list:
        """Returns list of all rows in database.

        :return: List of all rows in database.
        :rtype: list

        """
        return self.curs.execute("SELECT * FROM {}".format(self.table)).fetchall()

    def get_random_row(self, count: int = 1) -> list:
        """Gets a random row from the database.

        :param count: Number of rows to return
        :type count: int
        :return: List of rows
        :rtype: list

        """
        # TODO: turn the return into an object
        return self.curs.execute("SELECT * FROM {} ORDER BY RANDOM() LIMIT {}".format(self.table, count)).fetchall()

    def delete_by_raw_id(self, raw_id_to_delete: str) -> Optional[str]:
        """Delete a row by its raw_id

        :param raw_id_to_delete: The raw_id of the map to delete from database.
        :type raw_id_to_delete: str
        :return: Error message
        :rtype: str

        """
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

    def close(self) -> None:
        """Closes Database"""
        self.conn.commit()
        self.conn.close()

    def get_row_by_raw_id(self, raw_id: str) -> Union[list, tuple]:
        """Gets a map row by raw_id

        :param raw_id:
        :type raw_id: str
        :return: Returns a row
        :rtype: list

        """
        # TODO: return a maprow object instead of list!!
        my_row = self.curs.execute("""SELECT * FROM {} WHERE raw_id='{}'""".format(
            self.table,
            raw_id
            )).fetchall()
        if len(my_row) > 0:
            return my_row[0]
        return my_row


class HistoryDB(MapDB):
    """Database of Day in History Maps"""

    def __init__(self, table: str = 'historymaps', path: str = 'data/mapporn.db') -> None:
        """Construction method for HistoryDB

        :param table: historymaps table
        :type table: str
        :param path: path on local disk
        :type path: str

        """
        MapDB.__init__(self, table, path)

    def get_rows_by_date(self, date: int) -> list:
        """Gets a list of row by date (1-365)

        :param date: Date number between 1-365
        :type date: int
        :return: List of Maprow Objects
        :rtype: list

        """
        assert isinstance(date, int)
        rows_list = [x for x in (self.curs.execute("SELECT * FROM {} WHERE day_of_year = {}".format(self.table, date)))]
        obj_list = []
        if len(rows_list) > 0:
            for i in range(len(rows_list)):
                my_row = MapRow(schema=self.schema, row=rows_list[i], table=self.table)
                obj_list.append(my_row)
        return obj_list

    def change_date(self, raw_id: str, new_date: int) -> None:
        """Changes date of row in database using raw_id

        :param raw_id:
        :type raw_id: str
        :param new_date:
        :type new_date: int

        """
        self.curs.execute("UPDATE {} SET day_of_year={} WHERE raw_id='{}'".format(self.table, new_date, raw_id))
        self.conn.commit()

    def add_row_to_db(self, raw_id: str, text: str, day_of_year: int) -> None:
        """Adds row to HistoryDB

        :param raw_id:
        :type raw_id: str
        :param text: Title of map
        :type text: str
        :param day_of_year:
        :type day_of_year: int

        """
        self.curs.execute('''INSERT INTO {table} values("{raw_id}", "{text}", {day_of_year})'''
                          .format(table=self.table,
                                  raw_id=raw_id,
                                  text=text,
                                  day_of_year=day_of_year))
        self.conn.commit()

    def check_integrity(self) -> str:
        """A suite of tests to ensure integrity of HistoryDB"""
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

        if status == '':
            return 'PASS: {} integrity test passed.'.format(self.table)
        else:
            return status


class SocMediaDB(MapDB):
    """Database of general maps for posting to social media.

    Subclass of MapDB. This is a database containing a multitude of maps. Every three hours a map will be
        chosen from this database and published to social media. After the map is published it will be marked as "not
        fresh". After a set amount of time (around 400 days) the map can be "re-freshed". At any given time this
        database will contain a number of 'fresh' maps that are queued up.

        The maps also have a time zone associated with them for publishing at a target time of the day. Every three
        hours the script soc_media_stack.py is run and choses a fresh map to publish to social media.

    """

    def __init__(self, table: str = 'socmediamaps', path: str = 'data/mapporn.db') -> None:
        """Constructor for the SocMediaDB

        :param table:
        :type table: str
        :param path:
        :type path: str

        """
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
    def get_time_zone(cls, title_str: str) -> int:
        """Method takes a string and returns a time zone

        The method tries to match substrings from the title string to entries in a CSV.
            - For example if it finds the word "London" in the title string, it will return London's UTC time zone

        :param title_str:
        :type title_str:
        :return: UTC time zone
        :rtype: int

        """
        with open('data/locationsZone.csv', 'r') as f:
            csv_reader = csv.reader(f)
            zonedict = {rows[0].upper(): rows[1] for rows in csv_reader}
        this_zone = 99
        for place in zonedict:
            if place in functions.strip_punc(title_str.upper()):
                this_zone = int(zonedict[place])
        return this_zone

    def get_rows_by_time_zone(self, time_zone: int, fresh: Union[int, str] = 1) -> list:
        """Return a list of all the rows in a time zone

        :param time_zone:
        :type time_zone: int
        :param fresh:
        :type fresh: int
        :return:
        :rtype: list

        """
        if isinstance(time_zone, int):
            return [x for x in (self.curs.execute("SELECT * FROM {} WHERE time_zone = {} AND fresh = {}"
                                                  .format(self.table, time_zone, fresh)))]
        elif isinstance(time_zone, list):
            time_zone_list = []
            for i in time_zone:
                for j in self.curs.execute("SELECT * FROM {} WHERE fresh={} and time_zone={}"
                                           .format(self.table, fresh, i)):
                    time_zone_list.append(j)
            # TODO: return a list of MapRow objects
            return time_zone_list
        else:
            print(str(time_zone) + " is not a valid time zone")

    def change_time_zone(self, raw_id: str, new_zone: int) -> None:
        """Change the time zone by raw_id

        :param raw_id:
        :type raw_id:
        :param new_zone:
        :type new_zone: int

        """
        self.curs.execute("UPDATE {} SET time_zone = {} WHERE raw_id = '{}'".format(
            self.table,
            new_zone,
            raw_id))
        self.conn.commit()

    def update_to_not_fresh(self, raw_id: str) -> None:
        """Make a row not fresh anymore. Also uses the current time as date_posted

        :param raw_id:
        :type raw_id: str

        """
        self.curs.execute("UPDATE {} SET fresh=0 WHERE raw_id='{}'".format(self.table, raw_id))
        self.curs.execute("UPDATE {} SET date_posted={} WHERE raw_id='{}'"
                          .format(self.table, (int(time.time())), raw_id))
        self.conn.commit()

    def get_one_map_row(self, target_zone: int) -> object:
        """Gets one fresh map row from the database

        :param target_zone:
        :type target_zone: int
        :return: MapRow
        :rtype: object

        """
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

    def add_row_to_db(self,
                      raw_id: str,
                      text: str,
                      time_zone: int,
                      fresh: int = 1,
                      date_posted: Union[str, int] = 'NULL',
                      post_error: int = 0) -> None:
        """Adds row to database

        :param raw_id:
        :type raw_id: str
        :param text:
        :type text: str
        :param time_zone:
        :type time_zone: int
        :param fresh:
        :type fresh: int
        :param date_posted:
        :type date_posted: str or int
        :param post_error:
        :type post_error: int

        """
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

    def check_if_already_in_db(self, raw_id: str) -> bool:
        """Checks if map is already in database

        :param raw_id:
        :type raw_id: str
        :return:
        :rtype: bool

        """
        if len(self.curs.execute("SELECT * FROM {} WHERE raw_id = '{}'".format(self.table, raw_id)).fetchall()) >= 1:
            return True
        else:
            return False

    def check_integrity(self) -> str:
        """Checks Integrity of Database"""
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
            assert len(self._get_duplicates()) == 0
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

    def make_fresh_again(self, current_time: int, limit: int = 10) -> None:
        """Looks for rows older than a certain time and makes a number of them fresh again.

            Time past is set as 500 days, can be changed as needed.

        :param current_time:
        :type current_time: int
        :param limit:
        :type limit: int

        """
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

    def _get_duplicates(self) -> list:
        """Gets a list of duplicates

        This code is probably unnecessary, but can be useful if somehow a duplicate gets into the database.

        :return:
        :rtype: list
        """
        return self.curs.execute("""SELECT raw_id, count(*) FROM {} GROUP BY raw_id HAVING count(*) > 1""".format(
            self.table)).fetchall()

    def __remove_duplicates(self) -> None:
        """Private Method: Removes duplicates from the database

        This code is probably unnecessary, but can be useful if somehow a duplicate gets into the database.
        It does some complex actions on the database and shouldn't accidentally be used, therefore it's
        a private method.

        """
        source_db_path: str = 'data/mapporn.db'
        test_db_path: str = 'data/test.db'
        # noinspection PyTypeChecker
        copyfile(source_db_path, test_db_path)

        soc_db = SocMediaDB(path=test_db_path)
        duplicates_count = len(soc_db._get_duplicates())
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
        assert len(soc_db._get_duplicates()) == 0
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
    """Database of logs

    Keeps records of successes and failures in of scripts in the form of diagnostics dictionaries
    which are converted to and from Diagnostic objects.

    """

    def __init__(self, table: str = 'logging', path: str = 'data/mapporn.db') -> None:
        """

        :param table:
        :type table: str
        :param path:
        :type path: str
        """
        MapDB.__init__(self, table, path)

    def add_row_to_db(self, diagnostics: dict, passfail: int, error_text: str = None) -> None:
        """Adds a diagnostics row to logging database

        :param diagnostics:
        :type diagnostics: dictionary
        :param passfail: 1 for pass, 0 for fail
        :type passfail: int
        :param error_text:
        :type error_text: str

        """
        my_sql = '''INSERT INTO logging (date, error_text, diagnostics, passfail) VALUES (?, ?, ?, ?)'''
        my_list = [int(time.time()), str(error_text), str(diagnostics), passfail]
        self.curs.execute(my_sql, my_list)
        self.conn.commit()

    def get_fails_previous_24(self, current_time: int) -> list:
        """Get all failed scripts from the last 24 hours

        :param current_time: A little longer than 24 hours to ensure it doesn't miss any edge cases.
        :type current_time: int
        :return: List of failures
        :rtype: list

        """
        current_time = int(current_time)
        assert len(str(current_time)) == 10
        twenty_four_ago = int(current_time) - 87500
        return list(row for row in self.curs.execute(
            "SELECT * FROM {} WHERE passfail = 0 AND date >= {}"
            .format(self.table, twenty_four_ago)
        ))

    def get_fails_in_window(self, newer_time: int, older_time: int) -> list:
        """Get log of failures over a window of time. Usually used for troubleshooting

        :param newer_time:
        :type newer_time: int
        :param older_time:
        :type older_time: int
        :return: List of fails
        :rtype: list

        """
        newer_time = int(newer_time)
        older_time = int(older_time)
        return list(row for row in self.curs.execute(
            "SELECT * FROM {} WHERE passfail = 0 AND date >= {} AND date <= {}"
            .format(self.table,
                    older_time,
                    newer_time)
        ))

    def get_successes_previous_24(self, current_time: int) -> list:
        """Get successful script executions from last 24 hours.

        :param current_time:
        :type current_time: int
        :return:
        :rtype: list

        """
        current_time = int(current_time)
        assert len(str(current_time)) == 10
        # Note: capturing all fails from a little longer than 24 hours ago
        # to ensure it doesn't miss any fails from previous day's script.
        twenty_four_ago = int(current_time) - 87500
        return list(row for row in self.curs.execute(
            "SELECT * FROM {} WHERE passfail = 1 AND date >= {}"
            .format(self.table, twenty_four_ago)
        ))

    def get_fails_by_script(self, script: str) -> list:
        """Get failures by script name

        :param script:
        :type script: str
        :return:
        :rtype: list

        """
        print("Returning list of all fails from {}".format(script))
        return list(row for row in self.curs.execute(
            "SELECT * WHERE passfail = 0 AND diagnostics LIKE '{}'"
            .format(script)
        ))

    def check_integrity(self) -> str:
        """

        :return: Status of integrity check.
        :rtype: str

        """
        status = ''
        try:
            for i in self.all_rows_list():
                assert isinstance(i[0], int)
                assert i[3] == 1 or i[3] == 0
                if i[2] is None:
                    raise AssertionError
                this_diag = Diagnostic.diag_dict_to_obj(i[2])
                assert str(this_diag.script).endswith(".py")
        except AssertionError as e:
            status += 'Error encountered: {}\n'.format(str(e))
        try:
            assert isinstance(self.get_fails_previous_24(current_time=int(time.time())), list)
            assert isinstance(self.get_successes_previous_24(current_time=int(time.time())), list)
        except AssertionError as e:
            status += '* previous 24 methods did not return lists.\n    {}\n\n'.format(str(e))
        if status == '':
            return "PASS: LoggingDB integrity test passed."
        else:
            print(status)
            return status


class JournalDB(MapDB):
    """Database keeping a daily journal of results of status.py script exection"""
    def __init__(self, table: str = 'journal', path: str = 'data/mapporn.db') -> None:
        """Constructor for JournalDB

        :param table:
        :type table: str
        :param path:
        :type path: str

        """
        MapDB.__init__(self, table, path)

    def update_todays_status(self, benchmark_time: int) -> None:
        """Updates today's status in the database

        :param benchmark_time: Time it takes the script to run.
        :type benchmark_time: int

        """
        # TODO: verify this is working after errors start getting added to my_dict
        # right now I don't know if the my_dict is working.
        date = time.time()
        hist_db = HistoryDB()
        log_db = LoggingDB()
        soc_db = SocMediaDB()
        # TODO: do i need these three lines for massaging my_dict??
        my_dict = {i[0]: str(i[1:]).replace('"', "\\'") for i in log_db.get_fails_previous_24(int(date))}
        my_dict = str(my_dict)
        my_dict = my_dict.replace('"', '\'')
        query = """INSERT INTO {table} values(?, ?, ?, ?, ?, ?, ?, ?, ?)""".format(table=self.table)
        self.curs.execute(query, (date,
                                  len(hist_db),
                                  len(log_db),
                                  len(soc_db),
                                  soc_db.fresh_count,
                                  len(log_db.get_fails_previous_24(int(date))),
                                  len(log_db.get_successes_previous_24(int(date))),
                                  benchmark_time,
                                  str(my_dict)))
        self.conn.commit()

    def check_integrity(self) -> str:
        """Checks the integrity of logging database

        :return: status of database integrity
        :rtype: str

        """
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
        if status == '':
            return "PASS: JournalDB integrity test passed."
        else:
            print(status)
            return status

    def average_benchmark_times(self) -> int:
        """Calculates the average time it takes to run status.py

        :return: average time
        :rtype: int

        """
        my_sum = 0
        counter = 0
        for i in self.all_rows_list():
            if i[4] > 0:
                counter += 1
                my_sum += int(i[4])
        return my_sum / counter


class ContestDB(MapDB):
    """Database Object for tracking submissions to the monthly map contest."""

    def __init__(self, table: str = 'contest', path: str = 'data/mapporn.db') -> None:
        MapDB.__init__(self, table, path)

    def add_to_contest(self, map_name: str, url: str, desc: str, author: str, raw_id: str) -> None:
        """Adds map row to contest database

        :param map_name: Name of submitted map
        :type map_name: str
        :param url: URL to map
        :type url: str
        :param desc: User submitted description of map
        :type desc: str
        :param author: Author of map (username)
        :type author: str
        :param raw_id: Message ID
        :type raw_id: str

        """
        sql = ''' INSERT INTO contest(map_name,url,desc,author,raw_id) 
                  VALUES(?,?,?,?,?) '''
        map_submission = (map_name, url, desc, author, raw_id)
        self.curs.execute(sql, map_submission)
        self.conn.commit()

    def add_date_to_submission(self, raw_id: str, yearmonth: int) -> None:
        """Adds the Month that the map was voted on

        :param raw_id: message ID
        :type raw_id: str
        :param yearmonth: YYYYMM integer
        :type yearmonth: int

        """
        assert len(str(yearmonth)) == 6 and type(yearmonth) == int
        sql = ''' UPDATE contest
                  SET cont_date = ?
                  WHERE raw_id = ?'''
        self.curs.execute(sql, (yearmonth, raw_id))
        self.conn.commit()

    def add_vote_count_to_submission(self, raw_id: str, votecount: int) -> None:
        """Adds the vote total for the map after the contest finishes

        :param raw_id: message ID
        :type raw_id: str
        :param votecount: Count of upvotes for the map
        :type votecount: int

        """
        sql = ''' UPDATE contest
                  SET votes = ?
                  WHERE raw_id = ?'''
        self.curs.execute(sql, (votecount, raw_id))
        self.conn.commit()

    def check_if_already_in_db(self, raw_id: str) -> bool:
        """Checks if map is already in database

        :param raw_id: message id
        :type raw_id: str
        :return: True if in database, false if not in database
        :rtype: bool

        """
        if len(self.curs.execute("SELECT * FROM {} WHERE raw_id = '{}'".format(self.table, raw_id)).fetchall()) >= 1:
            return True
        else:
            return False

    def get_sorted_top_of_month(self, month: int) -> List[object]:
        """Gets a list of MapRow objects sorted by most voted for a given mont

        :param month: YYYYMM format
        :type month: int
        :return: List of MapRow objects
        :rtype: list

        """
        assert len(str(month)) == 6
        sql = '''SELECT * FROM contest WHERE cont_date = {}'''.format(month)
        row_list = []
        for i in self.curs.execute(sql).fetchall():
            row_list.append(MapRow(schema=self.schema, row=i, table=self.table))
        row_list.sort(key=lambda x: x.votes, reverse=True)
        return row_list


class ShotgunBlast:
    """Class for blasting a post to multiple social media sites at once.

    Currently this posts to Twitter, Facebook and Tumblr

    """

    def __init__(self, praw_obj: object, title: str = None, announce_input: str = None) -> None:
        """Constructor for ShotgunBlast

        :param praw_obj: PRAW object
        :type praw_obj: obj
        :param title: post title
        :type title: str
        :param announce_input: An optional announcement, usually defaults to None
        :type announce_input: str

        """
        self.announce_input = announce_input
        self.twitter_max = 280
        self.praw_obj = praw_obj
        self.shortlink = praw_obj.shortlink
        self.title = self.get_title(title)
        self.image_url = self.praw_obj.url
        self.raw_id = self.praw_obj.id

    @classmethod
    def get_hashtag_locations(cls, string: str) -> str:
        """Adds a hashtag to locations in title that are also in an external csv

        For example - London returns #London

        :param string: title
        :type string: str
        :return: hashtagged location
        :rtype: str

        """
        my_hashes = ''
        string_list = string.split(' ')
        with open('data/locations.txt') as locationstext:
            locationstext = locationstext.read().split()
            for w in string_list:
                if str(w) in locationstext:
                    my_hashes += '#' + str(w) + ' '
        return my_hashes.rstrip()

    @classmethod
    def remove_text_inside_brackets(cls, text: str, brackets: str = "[]") -> str:
        """Removes text from inside brackets

        For example "My Map [1024x496] by Anonymous" returns "My Map by Anonymous"

        :param text: raw text to change
        :type text: str
        :param brackets:
        :type brackets: str
        :return: clean text
        :rtype: str

        """
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
    def init_shotgun_blast(cls) -> None:
        """Initializes Twitter for the shotgun blast"""
        global api

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        api = tweepy.API(auth)

    def get_title(self, raw_title: str) -> str:
        """Gets the raw title and makes it fit into Twitter's character limits

        :param raw_title:
        :type raw_title: str
        :return: string that is twitter length compliant
        :rtype: str

        """
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

    def download_image(self) -> str:
        """Downloads an image based on the object image_url attribute

        :return: filename (string)
        :rtype: str

        """
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
                assert request.status_code == 200
                with open(filename, 'wb') as image:
                    for chunk in request:
                        image.write(chunk)
                filesize = os.path.getsize('temp.jpg')
            if filesize > 3070000:
                os.remove(filename)
                filename = 'temp.jpg'
                url = self.praw_obj.preview['images'][0]['resolutions'][3][
                    'url']  # This is the smaller image. Using this because Twitter doesn't like huge files.
                request = requests.get(url, stream=True)
                assert request.status_code == 200
                with open(filename, 'wb') as image:
                    for chunk in request:
                        image.write(chunk)
            return filename
        except AssertionError as e:
            raise Exception('Could not download image!    \n{}    \n\n'.format(str(e)))

    def post_to_all_social(self) -> dict:
        """Posts object to all social media.

        :return: Dictionary with (str) urls to Twitter, Facebook, Tumblr
        :rtype: dict

        """
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

    def check_integrity(self) -> str:
        """Checks integrity of class

        :return: status message
        :rtype: str

        """
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
                    == 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque nec magna luctus, ' \
                       'vestibulum ' \
                       'diam sed, condimentum ante. Sed pharetra blandit tortor, non tempus ex suscipit vel. Nulla ' \
                       'facilisi. Quisque orci est, aliquam in ornare ac, scelerisque quis du... ' + self.shortlink
            # Test title input of length 245 (280 - shortlink length). Should include #MapPorn
                assert (self.get_title(raw_title='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc '
                                       'facilisis turpis ante, eget pellentesque Quebec sagittis sed. Nullam vel '
                                                 'finibus metus. Aenean bibendum, nisl nec varius ultrices, augue '
                                                 'arcu rutrum nunc, vel pharetra justo lorem vel yz')) \
                    == 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis turpis ante, eget ' \
                       'pellentesque Quebec sagittis sed. Nullam vel finibus metus. Aenean bibendum, nisl nec varius ' \
                       'ultrices, augue arcu rutrum nunc, vel pharetra justo lorem vel yz ' + \
                       self.shortlink + ' #MapPorn'
            # Test title input with location hashtag
                assert (self.get_title(raw_title='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc '
                                                 'facilisis turpis ante, eget pellentesque tellus sagittis sed. '
                                                 'Nullam vel finibus metus. Aenean bibendum, nisl nec varius '
                                                 'ultrices, augue arcu rutrum nunc, vel pharetra justo lore London')) \
                    == 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc facilisis turpis ante, eget ' \
                       'pellentesque tellus sagittis sed. Nullam vel finibus metus. Aenean bibendum, nisl nec varius ' \
                       'ultrices, augue arcu rutrum nunc, vel pharetra justo lore #London ' + \
                       self.shortlink + ' #MapPorn'
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
    """Class for creating generic social media posts - not from Reddit"""

    def __init__(self, filename: str, title: str) -> None:
        """Constructor for GenericPost class

        :param filename:
        :type filename: str
        :param title:
        :type title: str

        """
        self.filename = filename
        self.title = title

    def post_to_all_social(self) -> dict:
        """Posts to Twitter, Tumblr, Facebook

        :return: dictionary of (str) social media URLS
        :rtype: dict

        """
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


hist_schema = OrderedDict([('raw_id', 'TEXT'),
                           ('text', 'TEXT'),
                           ('day_of_year', 'NUMERIC')])

soc_schema = OrderedDict([('raw_id', 'TEXT'),
                          ('text', 'TEXT'),
                          ('time_zone', 'NUMERIC'),
                          ('fresh', 'NUMERIC'),
                          ('date_posted', 'DATE'),
                          ('post_error', 'NUMERIC')])

log_schema = OrderedDict([('date', 'NUMERIC'),
                          ('error_text', 'TEXT'),
                          ('diagnostics', 'TEXT'),
                          ('passfail', 'NUMERIC')])

jour_schema = OrderedDict([('date', 'NUMERIC'),
                           ('hist_rows', 'NUMERIC'),
                           ('log_rows', 'NUMERIC'),
                           ('soc_rows', 'NUMERIC'),
                           ('fresh_rows', 'NUMERIC'),
                           ('errors_24', 'NUMERIC'),
                           ('successes_24', 'NUMERIC'),
                           ('benchmark_time', 'REAL'),
                           ('dict', 'TEXT')])

cont_schema = OrderedDict([('map_name', 'TEXT'),
                           ('url', 'TEXT'),
                           ('desc', 'TEXT'),
                           ('author', 'TEXT'),
                           ('raw_id', 'TEXT'),
                           ('votes', 'NUMERIC'),
                           ('cont_date', 'NUMERIC')])

schema_dict = {'journal': jour_schema,
               'logging': log_schema,
               'socmediamaps': soc_schema,
               'historymaps': hist_schema,
               'contest': cont_schema}
