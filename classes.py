import ast
from collections import OrderedDict
import random
import sqlite3
import time


class MapRow:
    def __init__(self, schema, row):
        self.schema = schema.keys()
        self.row = row
        if len(self.row) != len(self.schema):
            raise ValueError("schema size and row size must be equal")
        self.dict = dict(zip(self.schema, self.row))

    def date(self):
        try:
            self.dict['day_of_year']
        except KeyError:
            print("No information for day_of_year")
            return
        import datetime
        dt = datetime.datetime(2010, 1, 1)
        dtdelta = datetime.timedelta(days=self.dict['day_of_year'])
        return (dt + dtdelta).strftime('%Y/%m/%d')


class Diagnostic:
    def __init__(self, script, raw_id=None, severity=None, table=None, traceback=None, tweet=None):
        self.raw_id = raw_id
        self.script = script
        self.severity = severity
        self.table = table
        self.traceback = traceback
        self.tweet = tweet

    def make_dict(self):
        return {
            "raw_id": self.raw_id,
            "script": self.script,
            "severity": self.severity,
            "table": self.table,
            "traceback": self.traceback,
            "tweet": self.tweet
        }


def diag_dict_to_obj(diag_dict):
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
    return my_diag


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

    def all_rows_list(self):
        return self.curs.execute("SELECT * FROM {}".format(self.table)).fetchall()

    def close(self):
        self.conn.commit()
        self.conn.close()


class HistoryDB(MapDB):
    def __init__(self, table='historymaps', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)

    def get_rows_by_date(self, date):
        assert isinstance(date, int)
        return [x for x in (self.curs.execute("SELECT * FROM {} WHERE day_of_year = {}".format(self.table, date)))]

    def change_date(self, raw_id, new_date):
        self.curs.execute("UPDATE {} SET day_of_year={} WHERE raw_id='{}'".format(self.table, new_date, raw_id))
        self.conn.commit()

    def add_row_to_db(self, raw_id, text, day_of_year):
        self.curs.execute("INSERT INTO {table} values("
                          "'{raw_id}', '{text}', {day_of_year})"
                          .format(table=self.table,
                                  raw_id=raw_id,
                                  text=text,
                                  day_of_year=day_of_year))
        self.conn.commit()

    def check_integrity(self):
        status = ''
        for i in self.all_rows_list():
            try:
                assert isinstance(i[2], int) and (0 < i[2] < 366)
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
        if status == '':
            return 'PASS: {} integrity test passed.'.format(self.table)
        else:
            return status


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
        if min_target < -11:
            min_target += 24
        elif max_target > 12:
            max_target -= 24
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
        random_int = random.randint(0, (len(filtered_map_list) - 1))
        my_row = filtered_map_list[random_int]
        return MapRow(schema=self.schema, row=my_row)

    def add_row_to_db(self, raw_id, text, time_zone, fresh=1, post_error=0):
        self.curs.execute("INSERT INTO {table} values("
                          "'{raw_id}', '{text}', {time_zone}, {fresh}, NULL, {post_error})"
                          .format(table=self.table,
                                  raw_id=raw_id,
                                  text=text,
                                  time_zone=time_zone,
                                  fresh=int(fresh),
                                  post_error=int(post_error)))
        self.conn.commit()

    def check_integrity(self):
        status = ''
        for i in self.all_rows_list():
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
            try:
                assert (-10 <= int(i[2]) <= 12) or int(i[2]) == 99
            except AssertionError as e:
                status += "* time_zone of {} in {} is not acceptable\n  {}\n\n".format(
                    i[0], self.table, e
                )
            try:
                assert (int(i[3]) == 0) or (int(i[3]) == 1)
            except AssertionError as e:
                status += "* fresh of {} is not a boolean in {}\n  {}\n\n".format(
                    i[0], self.table, e
                )
            try:
                if int(i[3]) == 0:
                    assert len(str(i[4])) >= 10
            except AssertionError as e:
                status += "* Item {} is not fresh and does not have a date_posted date\n  {}\n\n".format(
                    i[0], e
                )
            try:
                if i[3] == 0:
                    assert int(i[4]) >= (time.time() - 37500000)
            except Exception as e:
                status += "* Item {} has a date_posted older than a year.\n  {}\n\n".format(
                    i, e
                )
        if status == '':
            return 'PASS: {} integrity test passed.'.format(self.table)
        else:
            return status

    def make_fresh_again(self, current_time):
        assert len(str(int(current_time))) == 10
        time_past = 34560000
        cutoff_time = (current_time - int(time_past))
        for i in self.all_rows_list():
            if (isinstance(i[3], int)) and (int(i[3]) == 0):
                if int(i[4]) <= cutoff_time:
                    self.curs.execute("UPDATE {} SET fresh=1 WHERE raw_id='{}'".format(
                        self.table, i[0]
                    ))
                    self.conn.commit()
        self.conn.close()

    def get_row_by_raw_id(self, raw_id):
        return self.curs.execute("""SELECT * FROM {} WHERE raw_id='{}'""".format(
            self.table,
            raw_id
        )).fetchall()


class LoggingDB(MapDB):
    def __init__(self, table='logging', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)

    def add_row_to_db(self, diagnostics, passfail, error_text=None):
        self.curs.execute('''INSERT INTO {table} values({time}, '{error_text}', "{diag}", {passfail})'''.format(
            table=self.table,
            time=int(time.time()),
            error_text=error_text,
            diag=str(diagnostics),
            passfail=passfail
        ))
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
                this_diag = diag_dict_to_obj(i[2])
                assert str(this_diag.script).endswith(".py")
        except AssertionError as e:
            status += 'Error encountered: {}\n'.format(e)
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
        my_dict = {i[0]: str(i[1:]).replace('"', "\\'") for i in log_db.get_fails_previous_24(date)}
        my_dict = str(my_dict)
        print(my_dict)
        my_dict = my_dict.replace('"', '\'')
        print(my_dict)
        query = """INSERT INTO {table} values(?, ?, ?, ?, ?, ?, ?, ?, ?)""".format(table=self.table)
        self.curs.execute(query, (date,
                                  hist_db.rows_count,
                                  log_db.rows_count,
                                  soc_db.rows_count,
                                  soc_db.fresh_count,
                                  len(log_db.get_fails_previous_24(date)),
                                  len(log_db.get_successes_previous_24(date)),
                                  benchmark_time,
                                  str(my_dict)))

    def check_integrity(self):
        #TODO add more integrity checks
        for i in self.all_rows_list():
            assert isinstance(i[0], int)
            assert isinstance(i[1], int)
            assert isinstance(i[2], int)
            assert isinstance(i[3], int)
            assert isinstance(i[4], int)
            assert isinstance(i[7], (int, float))

        assert self.schema == OrderedDict([('date', 'NUMERIC'),
                                          ('hist_rows', 'NUMERIC'),
                                          ('log_rows', 'NUMERIC'),
                                          ('soc_rows', 'NUMERIC'),
                                          ('fresh_rows', 'NUMERIC'),
                                          ('errors_24', 'NUMERIC'),
                                          ('successes_24', 'NUMERIC'),
                                          ('benchmark_time', 'REAL'),
                                          ('dict', 'TEXT')])

    def average_benchmark_times(self):
        my_sum = 0
        counter = 0
        for i in self.all_rows_list():
            if i[4] > 0:
                counter += 1
                my_sum += int(i[4])
        return my_sum / counter
