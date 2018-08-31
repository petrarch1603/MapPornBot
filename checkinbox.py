from classes import *
import csv
from functions \
    import my_reddit_ID, bot_disclaimer, SubmissionObject, strip_punc, send_reddit_message_to_self
import os
import praw


def init():
    global hist_db, log_db, my_diag, r, soc_db
    print("Running checkinbox.py")
    hist_db = HistoryDB()
    log_db = LoggingDB()
    my_diag = Diagnostic(script=os.path.basename(__file__))
    r = praw.Reddit('bot1')
    soc_db = SocMediaDB()


init()
disclaimer = bot_disclaimer()
MessageReply = 'Your map has been received.   ' + '\n' + 'Look for the voting post for the contest soon.    ' + '\n' + \
               '&nbsp;       ' + '\n' + disclaimer


newMessage = 'false'

for message in r.inbox.unread():
    newMessage = 'true'

if newMessage is 'false':
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
    exit()


def get_time_zone(title_str):
    with open('data/locationsZone.csv', 'r') as f:
        csv_reader = csv.reader(f)
        zonedict = {rows[0].upper(): rows[1] for rows in csv_reader}
    this_zone = 99
    for place in zonedict:
        if place in title_str:
            this_zone = int(zonedict[place])
    if this_zone == 99:  # 99 is for maps that don't have a time zone associated with them
        my_message = ("No time zone parsed from this title.\n"
                      "Check it and see if there are any "
                      "locations to add to the CSV.\n" + str(title))
        send_reddit_message_to_self(title="No time zones found", message=my_message)
        this_zone = int(this_zone)
    return this_zone


for message in r.inbox.unread():
    if message.subject == "Map Contest Submission":
        # TODO add logging here
        # logdict['type'] = 'submissionReceived'
        # logdict['time'] = time.time()
        submission = message.body
        submission = os.linesep.join([s for s in submission.splitlines() if s])  # removes extraneous line breaks
        submission = submission.splitlines()  # Turn submission into a list
        submission = [w.replace('Link: ', '') for w in submission]  # Replace the text 'Link: ' with blankspace.
        submission.append(message.author)  # Add author value
        submission.append(message)  # Add unique value for the message. This is important for indexing later on.
        newmap = SubmissionObject(
            map_name=submission[0],
            map_url=submission[1],
            map_desc=(str(submission[2])),
            creator=(str(submission[3])),
            unique_message=(str(submission[4]))
        )
        # Now make that list a row a CSV
        with open('submissions.csv', 'a') as submitFile:
            reader = csv.reader(submitFile)
            wr = csv.writer(submitFile)
            wr.writerow(submission)
            message.reply(MessageReply)
            # Send a message to a human so that they can QC the CSV.
            r.redditor(my_reddit_ID).message('New Map added to CSV', 'A new map has been submitted. '
                                             'Check the CSV for formatting\n' + message.body)
        message.mark_read()
        newmap = newmap.toJSON()
        # logdict['object'] = newmap
        # addToMongo(logdict)

    elif message.subject == 'socmedia' and message.author == 'Petrarch1603':
        my_diag.table = 'socmediamaps'
        socmediamap = message.body
        socmediamap = os.linesep.join([s for s in socmediamap.splitlines() if s])  # removes extraneous line breaks
        socmediamap = socmediamap.splitlines()  # Turn submission into a list
        title = None
        try:
            assert socmediamap[0].startswith("https://redd.it/")
        except Exception as e:
            errorMessage = ("Error detected: Message does not include a valid URL" + str(message.body))
            my_diag.traceback = e
            my_diag.severity = 1
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=errorMessage)
            log_db.close()
            send_reddit_message_to_self(title="Socmedia Message Error", message=errorMessage)
        raw_id = socmediamap[0][-6:]
        my_diag.raw_id = raw_id
        try:
            if socmediamap[1]:
                title = socmediamap[1]
        except IndexError:
            title = r.submission(id=raw_id).title

        title = title.replace("\"", "'")
        my_zone = get_time_zone((strip_punc(title)).upper())

        # TODO make sure the submission isn't already added
        old_count = soc_db.rows_count
        soc_db.add_row_to_db(raw_id=raw_id, text=title, time_zone=int(my_zone))
        new_count = soc_db.rows_count
        try:
            assert int(new_count) == (int(old_count) + 1)
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
            log_db.close()
            message.mark_read()
        except AssertionError as e:
            errorMessage = "Error: new count did not go up by 1"
            my_diag.traceback = e
            my_diag.severity = 2
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=errorMessage)
            log_db.close()
            send_reddit_message_to_self(title="problem adding to DB", message=errorMessage)
            message.mark_read()

    elif message.subject == 'day_of_year' and message.author == 'Petrarch1603':
        my_diag.table = "historymaps"
        DIHmessage = message.body
        DIHmessage = os.linesep.join([s for s in DIHmessage.splitlines() if s])
        DIHmessage = DIHmessage.splitlines()
        print(DIHmessage)
        day_of_year = ''
        raw_id = ''
        text = ''
        for item in DIHmessage:
            try:
                item = int(item)
            except ValueError:
                pass
            if isinstance(item, int) and 0 < item < 366:
                day_of_year = item
                print("Day in history: " + str(day_of_year))
            elif item.startswith("https://redd.it/"):
                raw_id = item[-6:]
                my_diag.raw_id = raw_id
                print("Raw_ID: " + str(raw_id))
            else:
                text = item
                print("Text: " + str(text))
        if text == '' or raw_id == '' or day_of_year == '':
            errorMessage = 'Error: Missing parameters \n'
            for line in DIHmessage:
                errorMessage += (line + '\n')
            my_diag.traceback = errorMessage
            my_diag.severity = 1
            log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=errorMessage)
            log_db.close()
            send_reddit_message_to_self(title='Error processing day in history',
                                        message=errorMessage)
        else:
            try:
                hist_db.add_row_to_db(raw_id=raw_id, text=text, day_of_year=day_of_year)
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
            except Exception as my_e:
                my_error_message = "Could not add map to historymaps\n" \
                                   "Error: " + str(my_e) + "\n" \
                                                           "Post Title: " + str(text)
                my_diag.severity = 2
                my_diag.traceback = my_e
                log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=0, error_text=my_error_message)
                log_db.close()
                send_reddit_message_to_self(title="Could not add to day_of_year.db", message=my_error_message)
        message.mark_read()

    else:
        msg = message.body
        author = str(message.author)
        subject = message.subject
        r.redditor(my_reddit_ID).message('Message sent to Bot, Please check on it   \n', '*/u/' +
                                         author + '* sent this message to the bot. Please check on it.    \n' +
                                         '**Subject:** ' + subject + '     \n' + '**Message:**   \n' + msg)
        newMessageObject = {'author': author, 'subject': subject, 'body': msg}
        log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)
        log_db.close()
        message.mark_read()
