import classes
import datetime
import os


# This script will only be scoped to post from the socmedia table to social media.
# Checking the inbox and storing to the table will be done in checkinbox.py
print("Running social media stack script.")


def main():
    soc_db = classes.SocMediaDB()
    log_db = classes.LoggingDB()
    popular_hour = 9
    my_target_zone = get_target_hour(popular_hour)

    map_row = soc_db.get_one_map_row(target_zone=my_target_zone)
    map_row.post_to_social_media(table=soc_db.table, script=str(os.path.basename(__file__)))

    soc_db.close()
    log_db.close()


def get_target_hour(popular_hour_arg):
    utc_now = datetime.datetime.utcnow().hour
    target = popular_hour_arg - utc_now
    if target < -11:
        target += 22
    elif target > 12:
        target -= 22
    return target


if __name__ == '__main__':
    main()


# def postsocmedia(map_row):
#     """
#     Takes a map_row object and posts it to social media.
#
#     :param map_row: (obj) returned by soc_db.get_one_map_row().
#     :return: (str) error message or '' if successful.
#     """
#     my_diag = map_row.create_diagnostic(script=str(os.path.basename(__file__)))
#     my_diag.table = "socmediamaps"
#     error_message = ''
#
#     try:
#         s_b_dict = map_row.blast()
#         my_diag.tweet = s_b_dict['tweet_url']
#         log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
#     except classes.tweepy.TweepError as e:
#         this_diag = my_diag
#         try:
#             soc_db.close()
#         except classes.sqlite3.ProgrammingError as e:
#             functions.send_reddit_message_to_self(title='Error', message="sqlite error: {}".format(e))
#         init()
#         fresh_status = soc_db.get_row_by_raw_id(map_row.raw_id)[3]
#         error_message = "Problem with tweepy    \n{}    \n{}    \nNew fresh status: {}    \n"\
#             .format(str(e), str(map_row.raw_id), str(fresh_status))
#         this_diag.traceback = error_message
#         this_diag.severity = 1
#         log_db.add_row_to_db(diagnostics=this_diag.make_dict(), passfail=0)
#     except Exception as e:
#         error_message = ("Error Encountered: \n"
#                          "Could not post to social media.\n" + str(e) + "\nMap with problem: \n" + map_row['text'])
#         my_diag.traceback = error_message
#         my_diag.severity = 2
#         log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
#
#     return error_message
