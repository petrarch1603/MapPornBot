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
    map_row.post_to_social_media(script=str(os.path.basename(__file__)))

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
