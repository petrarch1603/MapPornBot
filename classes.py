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


class MapDB:
    def __init__(self, table, path='data/mapporn.db'):
        self.path = path
        self.table = table
        self.conn = sqlite3.connect(path)
        self.curs = self.conn.cursor()
        self.rows_count = self.curs.execute('SELECT count(*) FROM {}'.format(self.table)).fetchall()[0][0]
        schema_dic = {}
        self.curs.execute("PRAGMA TABLE_INFO('{}')".format(self.table))
        for tup in self.curs.fetchall():
            schema_dic[tup[1]] = tup[2]
        self.schema = OrderedDict(schema_dic)

    def get_schema(self):
        schema_dic = {}
        self.curs.execute("PRAGMA TABLE_INFO('{}')".format(self.table))
        for tup in self.curs.fetchall():
            schema_dic[tup[1]] = tup[2]
        self.schema = OrderedDict(schema_dic)

    def all_rows_list(self):
        return self.curs.execute("SELECT * FROM {}".format(self.table)).fetchall()

    def close(self):
        self.conn.close()


class HistoryDB(MapDB):
    def __init__(self, table='historymaps', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)

    def get_rows_by_date(self, date):
        return [x for x in (self.curs.execute("SELECT * FROM {} WHERE day_of_year = {}".format(self.table, date)))]

    def change_date(self, raw_id, new_date):
        try:
            self.curs.execute("UPDATE {} SET day_of_year={} WHERE raw_id='{}'".format(self.table, new_date, raw_id))
            self.conn.commit()
        except Exception as e:
            # TODO: add logging
            print("Could not update " + str(raw_id) + " to day_of_year: " + str(new_date) + ". " + "Error: " + str(e))


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

    def update_to_not_fresh(self, raw_id):
        try:
            self.curs.execute("UPDATE {} SET fresh=0 WHERE raw_id='{}'".format(self.table, raw_id))
            self.curs.execute("UPDATE {} SET date_posted={} WHERE raw_id='{}'"
                              .format(self.table, (int(time.time())), raw_id))
            self.conn.commit()
        except Exception as e:
            # TODO: logging
            print("Error: " + str(e) + " could not change fresh value on " + str(raw_id))

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
            # TODO: Choose the time zone that is most frequently in the database, not a random map
            my_row = self.curs.execute("SELECT * FROM {} WHERE fresh=1 ORDER BY RANDOM() LIMIT 1"
                                     .format(self.table)).fetchone()
        else:
            random_int = random.randint(0, (len(filtered_map_list) - 1))
            my_row = filtered_map_list[random_int]
        return MapRow(schema=self.schema, row=my_row)

    def add_row_to_db(self, raw_id, text, time_zone):
        # TODO: add method for adding a new row to db
        pass


class LoggingDB(MapDB):
    def __init__(self, table='logging', path='data/mapporn.db'):
        MapDB.__init__(self, table, path)
