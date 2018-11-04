import classes
import csv
import functions
import os
import praw
import time

disclaimer = functions.bot_disclaimer()
MessageReply = 'Your map has been received.   ' + '\n' + 'Look for the voting post for the contest soon.    ' + '\n' + \
               '&nbsp;       ' + '\n' + disclaimer


def init(path='data/mapporn.db'):
    global hist_db, log_db, r, soc_db
    hist_db = classes.HistoryDB(path=path)
    log_db = classes.LoggingDB(path=path)
    soc_db = classes.SocMediaDB(path=path)


def main():
    for message in r.inbox.unread():
        init()

        # # Map Contest Submissions
        my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))
        if message.subject == "Map Contest Submission":
            submission = contest_message(message=message)
            my_diag.table = 'contest'
            my_diag.title = submission[0]
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
            add_submission_to_csv(submission=submission)
            message.mark_read()

        # # Social Media Maps
        elif message.subject == 'socmedia' and message.author == 'Petrarch1603':
            my_diag.table = 'socmediamaps'
            socmedia_message(message=message)
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
            log_db.conn.commit()
            log_db.close()
            message.mark_read()

        # # Day in History Messages
        elif message.subject == 'dayinhistory' and message.author == 'Petrarch1603':
            my_diag.table = "historymaps"
            dayinhistory_message(message=message)
            message.mark_read()

        # # Catch any other message a random user might have sent to the bot
        else:
            other_message(message=message)
            message.mark_read()


def contest_message(message):
    submission = functions.split_message(message.body)
    submission = [w.replace('Link:', '') for w in submission]  # Replace the title 'Link: ' with blankspace.
    submission = [w.replace('Map Name:', '') for w in submission]
    for i, v in enumerate(submission):
        submission[i] = submission[i].lstrip().rstrip()
    submission.append(message.author)  # Add author value
    submission.append(message)  # Add unique value for the message. This is important for indexing later on.
    message.reply(MessageReply)
    return submission


def add_submission_to_csv(submission):
    message_to_me = 'A new map has been submitted. Check the CSV for formatting    \n'
    if len(submission) > 3:
        message_to_me += "**NOTE: the entry is not formatted properly!!**"
    with open('submissions.csv', 'a') as submitFile:
        wr = csv.writer(submitFile)
        wr.writerow(submission)
        # Send a message to a human so that they can QC the CSV.
        functions.send_reddit_message_to_self(title='New Map added to CSV',
                                              message=message_to_me)


def socmedia_message(message, path='data/mapporn.db'):
    init(path=path)
    socmediamap = functions.split_message(message.body)
    for i, v in enumerate(socmediamap):
        socmediamap[i] = socmediamap[i].lstrip().rstrip()
    title = None

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

    # Get title and clean it up
    try:
        if socmediamap[1]:
            title = socmediamap[1]
    except IndexError:
        title = r.submission(id=raw_id).title

    # Add option for making the map not fresh when added to database
    try:
        if str(socmediamap[2]) == '0':
            fresh_status = 0
            date_posted = int(time.time())
    except IndexError:
        pass

    # Remove double quotes, very important for inserting into database
    title = classes.ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))

    # Check if raw_id is already in soc_db
    try:
        assert soc_db.check_if_already_in_db(raw_id=raw_id) is False
    except AssertionError:
        message.mark_read()
        return

    # Add to soc_db
    try:
        old_count = soc_db.rows_count
        time_zone = functions.get_time_zone((functions.strip_punc(title)))
        if time_zone == 99 and path == 'data/mapporn.db':
            my_message = ("No time zone parsed from this title.    \n"
                          "Check it and see if there are any "
                          "locations to add to the CSV.    \n" + str(title))
            functions.send_reddit_message_to_self(title="No time zones found", message=my_message)
        init(path=path)
        soc_db.add_row_to_db(raw_id=raw_id,
                             text=title,
                             time_zone=time_zone,
                             fresh=int(fresh_status),
                             date_posted=date_posted)
        soc_db.conn.commit()
        soc_db.close()
        init(path=path)
        new_count = soc_db.rows_count
    except Exception as e:
        error_message = "Error: could not add to soc_db    \n{}    \n\n".format(e)
        message.mark_read()
        return error_message

    # Check that the soc_db row count increased
    try:
        assert int(new_count) == (int(old_count) + 1)
    except AssertionError as e:
        error_message = "Error: new count did not go up by 1    \n{}    \n\n".format(e)
        functions.send_reddit_message_to_self(title="problem adding to DB", message=error_message)
        message.mark_read()


def dayinhistory_message(message, path='data/mapporn.db'):
    init(path=path)
    # Split message into a list
    dih_message = functions.split_message(message.body)
    day_of_year = ''
    raw_id = ''
    title = ''

    # Parse Message
    for item in dih_message:

        try:
            item = int(item)
        except ValueError:
            pass
        if isinstance(item, int) and 0 < item < 366:
            day_of_year = item
        elif item.startswith("https://redd.it/"):
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

    # Try to add to hist_db
    try:
        title = classes.ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))
        old_hist_row_count = hist_db.rows_count
        hist_db.add_row_to_db(raw_id=raw_id, text=title, day_of_year=day_of_year)
        hist_db.conn.commit()
        hist_db.close()
        init(path=path)
        assert hist_db.rows_count == old_hist_row_count + 1
    except AssertionError as e:
        error_message = "Error: new count did not go up by 1    \n{}    \n\n".format(e)
        functions.send_reddit_message_to_self(title="problem adding to DB", message=error_message)
        message.mark_read()
    except Exception as e:
        error_message = "Could not add map to historymaps\n" \
                        "Error: " + str(e) + "\n" \
                                             "Post Title: " + str(title)
        functions.send_reddit_message_to_self(title="Could not add to day_of_year.db", message=error_message)


def other_message(message, path='data/mapporn.db'):
    msg = message.body
    author = str(message.author)
    subject = message.subject
    functions.send_reddit_message_to_self(title='Message sent to Bot, Please check on it',
                                          message='*/u/{author}* sent this message to the bot. '
                                                  'Please check on it.    \n**Subject:**{subj}     \n**Message:**   \n'
                                                  '{msg}'.format(author=author,
                                                                 subj=subject,
                                                                 msg=msg))
    log_db.conn.commit()
    log_db.close()
    init(path=path)
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
