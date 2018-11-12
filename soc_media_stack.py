"""Script for choosing a map from the right time zone and posting it to social media.

At the time of script execution the script will find which time zone in the world it is currently
9 AM. Then the script will find a map in the database that is near that time zone and post it to
social media sites.

Uses the socmedia database.

The maps are acquired and stored in the database with the checkinbox.py script.

"""

import classes
import datetime
import os

print("Running social media stack script.")


def main() -> None:
    """Main script: gets map and posts it to social media."""
    soc_db = classes.SocMediaDB()
    log_db = classes.LoggingDB()
    popular_hour = 9
    my_target_zone = get_target_hour(popular_hour)

    map_row: object = soc_db.get_one_map_row(target_zone=my_target_zone)
    map_row.post_to_social_media(script=str(os.path.basename(__file__)))

    soc_db.close()
    log_db.close()


def get_target_hour(popular_hour_arg: int) -> int:
    """Gets the place time zone in the world where it is currently the target hour

    :param popular_hour_arg: time of day when it's best to post to social media
    :type popular_hour_arg: int
    :return: current time zone where it is the target hour
    :rtype: int

    """
    utc_now = datetime.datetime.utcnow().hour
    target = popular_hour_arg - utc_now
    if target < -11:
        target += 22
    elif target > 12:
        target -= 22
    return target


if __name__ == '__main__':
    main()
