"""Script for checking Reddit Bot's Inbox

Checks for following message:

    * Map Contest Submission
    * Social Media Map
        Adds this map to the SocMedia database. Every three hours a map from this database is posted to social media.
    * Day in History map
    * All other messages sent from users to the bot.

"""
import classes
import csv
import functions
import os
import praw
import time

# TODO: add type annotations to functions

script = str(os.path.basename(__file__))
disclaimer = functions.bot_disclaimer()
MessageReply = 'Your map has been received.   ' + '\n' + 'Look for the voting post for the contest soon.    ' + '\n' + \
               '&nbsp;       ' + '\n' + disclaimer


def init(path: str = 'data/mapporn.db') -> None:
    """Initializes databases, Reddit bot

    :param path: database path
    :type path: str

    """
    global hist_db, log_db, r, soc_db
    hist_db = classes.HistoryDB(path=path)
    log_db = classes.LoggingDB(path=path)
    soc_db = classes.SocMediaDB(path=path)


def main() -> None:
    """Main script to check inbox"""

    for message in r.inbox.unread():
        init()

        # # Map Contest Submissions
        if message.subject == "Map Contest Submission":
            contest_message(message=message)
            message.mark_read()

        # # Social Media Maps
        elif message.subject == 'socmedia' and message.author == 'Petrarch1603':
            socmedia_message(message=message)
            message.mark_read()

        # # Day in History Messages
        elif message.subject == 'dayinhistory' and message.author == 'Petrarch1603':
            dayinhistory_message(message=message)
            message.mark_read()

        # # Catch any other message a random user might have sent to the bot
        else:
            other_message(message=message)
            message.mark_read()


def contest_message(message):
    """Parse the praw message object and create a list for each map contest submission

    :param message: praw message object
    :type message: obj
    :return: List of strings:
                * Url of map submission
                * Name of map
                * Description of map
                * Author of map
                * Unique identity of submission (derived from the six character praw message id)
    :rtype: list

    """

    message_to_me = 'A new map has been submitted. Check for formatting    \n'
    submission = functions.split_message(message.body)
    submission = [w.replace('Link:', '') for w in submission]  # Replace the title 'Link: ' with blankspace.
    submission = [w.replace('Map Name:', '') for w in submission]
    for i, v in enumerate(submission):
        submission[i] = submission[i].lstrip().rstrip()
    cont_db = classes.ContestDB()
    map_name = submission[0]
    url = submission[1]
    if len(submission) > 3:
        submission[2] = str(submission[2]) + '\n' + str(submission[3])
    desc = submission[2]
    author = message.author
    raw_id = str(message.id)
    my_list = [map_name, url, desc, author, raw_id]
    message_to_me += "Name|Submission\n-|-\n"
    message_to_me += "Map Name:|{}\n" \
                     "URL:|{}\n" \
                     "Desc:|{}\n" \
                     "Author:|{}\n" \
                     "Raw ID:|{}\n    \n".format(map_name, url, desc, author, raw_id)
    functions.send_reddit_message_to_self(title='New Map Submitted!',
                                          message=message_to_me)

    row_obj = classes.MapRow(schema=cont_db.schema, row=my_list, table=cont_db.table)
    row_obj.add_row_to_db(script=script)
    message.reply(MessageReply)
    message.mark_read()
    return my_list


def add_submission_to_csv(submission):
    """Processes the submission list and adds it to csv

    :param submission: List of strings:
                * Url of map submission
                * Name of map
                * Description of map
                * Author of map
                * Unique identity of submission (derived from the six character praw message id)
    :type submission: list

    """
    with open('submissions.csv', 'a') as submitFile:
        wr = csv.writer(submitFile)
        wr.writerow(submission)


def socmedia_message(message, path='data/mapporn.db'):
    """Parses social media message and adds it to SocMediaDB

    :param message: Praw message object
    :type message: obj
    :param path: path to database
    :type path: str

    """
    socmediamap = functions.split_message(message.body)
    for i, v in enumerate(socmediamap):
        socmediamap[i] = socmediamap[i].lstrip().rstrip()

    # Verify that there is a Reddit shortlink in the message
    try:
        assert socmediamap[0].startswith("https://redd.it/")
    except Exception as e:
        error_message = ("Error detected: Message does not include a valid URL   \n{}   \n\n".format(e) +
                         str(message.body))
        functions.send_reddit_message_to_self(title="Socmedia Message Error", message=error_message)
        message.mark_read()
        return

    # Get raw_id and set default values for fresh_status and date_posted
    raw_id = socmediamap[0][-6:]
    fresh_status = 1
    date_posted = 'NULL'
    post_error = 0
    table = 'socmediamaps'

    # Get title and clean it up - adjust fresh status if third line is 0
    if len(socmediamap) > 2 and str(socmediamap[2]) == '0':
        fresh_status = 0
        date_posted = int(time.time())
        title = socmediamap[1]
    elif len(socmediamap) > 1:
        title = socmediamap[1]
    else:
        r = praw.Reddit('bot1')  # Leave this line for testing (need to patch this call in unittests)
        title = r.submission(id=raw_id).title

    # Remove double quotes, very important for inserting into database
    title = classes.ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))

    # Get time_zone
    time_zone = functions.get_time_zone((functions.strip_punc(title)))
    if time_zone == 99 and path == 'data/mapporn.db':
        my_message = ("No time zone parsed from this title.    \n"
                      "Check it and see if there are any "
                      "locations to add to the CSV.    \n" + str(title))
        functions.send_reddit_message_to_self(title="No time zones found", message=my_message)

    # Put all the variables in the list to pass to MapRow
    my_maprow_list = [raw_id,
                      title,
                      time_zone,
                      fresh_status,
                      date_posted,
                      post_error]

    # Create MapRow Object and add to database
    my_maprow = classes.MapRow(schema=classes.schema_dict[table], row=my_maprow_list, table=table, path=path)
    try:
        my_maprow.add_row_to_db(script=script)
    except Exception as e:
        functions.send_reddit_message_to_self(title='error adding to database',
                                              message="Socmedia Script Problem: {}   \n{}".format(e, script))
    message.mark_read()


def dayinhistory_message(message, path='data/mapporn.db'):
    """Parses dayinhistory message and adds it to HistoryDB

    :param message: Praw message object
    :type message: obj
    :param path: database path
    :type path: str

    """
    # Split message into a list
    dih_message = functions.split_message(message.body)
    day_of_year = ''
    raw_id = ''
    title = ''
    table = 'historymaps'
    # Parse Message
    for item in dih_message:

        try:
            item = int(item)
        except ValueError:
            pass
        if isinstance(item, int) and 0 < item < 366:
            day_of_year = item
        elif str(item).startswith("https://redd.it/"):
            raw_id = item.lstrip().rstrip()[-6:]
        else:
            title = item

    # Validate all parameters are included
    if title == '' or raw_id == '' or day_of_year == '':
        error_message = 'Error: Missing parameters \n'
        for line in dih_message:
            error_message += (line + '\n')
        functions.send_reddit_message_to_self(title='Error processing day in history',
                                              message=error_message)
        message.mark_read()
        return
    title = classes.ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))

    # Create MapRow and add to database
    my_maprow_list = [raw_id, title, day_of_year]
    my_maprow = classes.MapRow(schema=classes.schema_dict[table], row=my_maprow_list, table=table, path=path)
    try:
        my_maprow.add_row_to_db(script=script)
    except Exception as e:
        functions.send_reddit_message_to_self(title='error adding to database',
                                              message="history Script Problem: {}   \n{}".format(e, script))
    message.mark_read()


def other_message(message):
    """Receives all other messages sent to bot, and passes it own to a human for further processing

    :param message: praw message object
    :type message: obj

    """
    msg = message.body
    author = str(message.author)
    subject = message.subject
    functions.send_reddit_message_to_self(title='Message sent to Bot, Please check on it',
                                          message='*/u/{author}* sent this message to the bot. '
                                                  'Please check on it.    \n**Subject:**{subj}     \n**Message:**   \n'
                                                  '{msg}'.format(author=author,
                                                                 subj=subject,
                                                                 msg=msg))
    message.mark_read()


if __name__ == '__main__':
    new_message = False
    r = praw.Reddit('bot1')
    init()
    for _ in r.inbox.unread():
        new_message = True
    if new_message is False:
        mydiag = classes.Diagnostic(script=str(os.path.basename(__file__)))
        mydiag.traceback = "No New Mail"
        log_db.add_row_to_db(diagnostics=mydiag.make_dict(), passfail=1)
        exit()
    main()
