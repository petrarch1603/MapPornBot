from classes import *
import csv
from functions import bot_disclaimer, strip_punc, send_reddit_message_to_self
import os
import praw

disclaimer = bot_disclaimer()
MessageReply = 'Your map has been received.   ' + '\n' + 'Look for the voting post for the contest soon.    ' + '\n' + \
               '&nbsp;       ' + '\n' + disclaimer


def init():
    global hist_db, log_db, r, soc_db
    hist_db = HistoryDB()
    log_db = LoggingDB()
    soc_db = SocMediaDB()


def get_time_zone(title_str):
    with open('data/locationsZone.csv', 'r') as f:
        csv_reader = csv.reader(f)
        zonedict = {rows[0].upper(): rows[1] for rows in csv_reader}
    this_zone = 99
    for place in zonedict:
        if place in strip_punc(title_str.upper()):
            this_zone = int(zonedict[place])
    return this_zone


def split_message(message_str):
    message_str = os.linesep.join([s for s in str(message_str).splitlines() if s])
    message_list = message_str.splitlines()
    return message_list


def main():
    for message in r.inbox.unread():
        init()
        my_diag = Diagnostic(script=os.path.basename(__file__))

        # Map Contest Submissions
        if message.subject == "Map Contest Submission":
            my_diag.table = 'contest'
            submission = split_message(message.body)
            submission = [w.replace('Link: ', '') for w in submission]  # Replace the title 'Link: ' with blankspace.
            my_diag.title = submission[0]
            submission.append(message.author)  # Add author value
            submission.append(message)  # Add unique value for the message. This is important for indexing later on.
            # Now make that list a row in a CSV
            with open('submissions.csv', 'a') as submitFile:
                wr = csv.writer(submitFile)
                wr.writerow(submission)
                message.reply(MessageReply)
                # Send a message to a human so that they can QC the CSV.
                send_reddit_message_to_self('New Map added to CSV',
                                            'A new map has been submitted. Check the CSV for formatting    \n{}    \n\n'
                                            .format(message.body))
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
            message.mark_read()

        # Social Media Maps
        elif message.subject == 'socmedia' and message.author == 'Petrarch1603':
            my_diag.table = 'socmediamaps'
            socmediamap = split_message(message.body)
            title = None

            # Verify that there is a Reddit shortlink in the message
            try:
                assert socmediamap[0].startswith("https://redd.it/")
            except Exception as e:
                error_message = ("Error detected: Message does not include a valid URL   \n{}   \n\n".format(e) +
                                 str(message.body))
                my_diag.traceback = error_message
                my_diag.severity = 2
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=error_message)
                log_db.conn.commit()
                log_db.close()
                init()
                send_reddit_message_to_self(title="Socmedia Message Error", message=error_message)
                continue

            # Get raw_id
            raw_id = socmediamap[0][-6:]
            my_diag.raw_id = raw_id

            # Get title and clean it up
            try:
                if socmediamap[1]:
                    title = socmediamap[1]
            except IndexError:
                title = r.submission(id=raw_id).title

            # Remove double quotes, very important for inserting into database
            title = ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))
            my_diag.title = title
            # Check if raw_id is already in soc_db
            try:
                assert soc_db.check_if_already_in_db(raw_id=raw_id) is False
            except AssertionError as e:
                error_message = "Map already in database    \n{}    \n\n".format(e)
                my_diag.traceback = error_message
                my_diag.severity = 1
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
                log_db.conn.commit()
                log_db.close()
                init()
                message.mark_read()
                continue

            # Add to soc_db
            try:
                old_count = soc_db.rows_count
                time_zone = get_time_zone((strip_punc(title)))
                if time_zone == 99:
                    my_message = ("No time zone parsed from this title.    \n"
                                  "Check it and see if there are any "
                                  "locations to add to the CSV.    \n" + str(title))
                    send_reddit_message_to_self(title="No time zones found", message=my_message)
                soc_db.add_row_to_db(raw_id=raw_id, text=title, time_zone=time_zone)
                soc_db.close()
                init()
                new_count = soc_db.rows_count
            except Exception as e:
                error_message = "Error: could not add to soc_db    \n{}    \n\n".format(e)
                my_diag.traceback = error_message
                my_diag.severity = 2
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0)
                log_db.conn.commit()
                log_db.close()
                init()
                message.mark_read()
                continue

            # Check that the soc_db row count increased
            try:
                assert int(new_count) == (int(old_count) + 1)
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
                log_db.conn.commit()
                log_db.close()
                init()
                message.mark_read()
                print('Successfully added to soc_db')
            except AssertionError as e:
                error_message = "Error: new count did not go up by 1    \n{}    \n\n".format(e)
                my_diag.traceback = error_message
                my_diag.severity = 2
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=error_message)
                log_db.conn.commit()
                log_db.close()
                init()
                send_reddit_message_to_self(title="problem adding to DB", message=error_message)
                message.mark_read()

        # Day in History Messages
        elif message.subject == 'dayinhistory' and message.author == 'Petrarch1603':

            # Split message into a list
            my_diag.table = "historymaps"
            dih_message = split_message(message.body)
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
                    raw_id = item[-6:]
                    my_diag.raw_id = raw_id
                else:
                    title = item

            # Validate all parameters are included
            my_diag.title = title
            if title == '' or raw_id == '' or day_of_year == '':
                error_message = 'Error: Missing parameters \n'
                for line in dih_message:
                    error_message += (line + '\n')
                my_diag.traceback = error_message
                my_diag.severity = 1
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=error_message)
                log_db.conn.commit()
                log_db.close()
                init()
                send_reddit_message_to_self(title='Error processing day in history',
                                            message=error_message)
                message.mark_read()
                continue
            else:
                # Try to add to hist_db
                try:
                    title = ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))
                    print(day_of_year)
                    print(title)
                    print(raw_id)
                    hist_db.add_row_to_db(raw_id=raw_id, text=title, day_of_year=day_of_year)
                    hist_db.conn.commit()
                    hist_db.close()
                    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
                    log_db.conn.commit()
                    log_db.close()
                    init()
                except Exception as e:
                    error_message = "Could not add map to historymaps\n" \
                                       "Error: " + str(e) + "\n" \
                                       "Post Title: " + str(title)
                    my_diag.severity = 2
                    my_diag.traceback = error_message
                    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=error_message)
                    log_db.conn.commit()
                    log_db.close()
                    init()
                    send_reddit_message_to_self(title="Could not add to day_of_year.db", message=error_message)

            message.mark_read()

        # Catch any other message a random user might have sent to the bot
        else:
            msg = message.body
            author = str(message.author)
            subject = message.subject
            send_reddit_message_to_self(title='Message sent to Bot, Please check on it',
                                        message='*/u/{author}* sent this message to the bot. '
                                                'Please check on it.    \n**Subject:**{subj}     \n**Message:**   \n'
                                                '{msg}'.format(author=author,
                                                               subj=subject,
                                                               msg=msg))
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
            log_db.conn.commit()
            log_db.close()
            init()
            message.mark_read()


if __name__ == '__main__':
    new_message = False
    r = praw.Reddit('bot1')
    init()
    for _ in r.inbox.unread():
        new_message = True
    if new_message is False:
        my_diag = Diagnostic(script=str(os.path.basename(__file__)))
        my_diag.traceback = "No New Mail"
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
        exit()
    main()
