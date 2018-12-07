'''Script for posting a map from This Day in History'''

import calendar
import classes
import datetime
import os
import random


def get_todays_date() -> int:
    """Returns today's date in Epoch Time

    :return: Today's date in Epoch Time
    :rtype: int

    """
    today_int = datetime.datetime.now().timetuple().tm_yday
    if today_int > 60 and calendar.isleap(datetime.datetime.now().year):
        today_int -= 1
    return today_int


def main():
    '''Main Script'''
    hist_db = classes.HistoryDB()
    today_list = hist_db.get_rows_by_date(get_todays_date())

    if len(today_list) == 0:
        my_diag = classes.Diagnostic(script=os.path.basename(__file__))
        my_diag.table = 'historymaps'
        log_db = classes.LoggingDB()
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
        log_db.close()
        exit()

    maprow = random.choice(today_list)
    maprow.post_to_social_media(script=os.path.basename(__file__))


if __name__ == '__main__':
    main()
