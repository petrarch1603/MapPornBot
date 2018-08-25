import os
import praw
import csv
from functions import my_reddit_ID, bot_disclaimer, SubmissionObject, addToMongo, send_reddit_message_to_self, \
    add_to_historydb
import datetime
import time
import json

r = praw.Reddit('bot1')
disclaimer = bot_disclaimer()
MessageReply = 'Your map has been received.   ' + '\n' + 'Look for the voting post for the contest soon.    ' + '\n' + \
               '&nbsp;       ' + '\n' + disclaimer
                # To Do: add contest date to the MessageReply, that way users know when the contest is.

logdict = {}
newMessage = 'false'

for message in r.inbox.unread():
    newMessage = 'true'

if newMessage is 'false':
    # TODO add new database logging
    exit()

for message in r.inbox.unread():
    if message.subject == "Map Contest Submission":
        # TODO add logging here
        #logdict['type'] = 'submissionReceived'
        #logdict['time'] = time.time()
        submission = message.body
        submission = os.linesep.join([s for s in submission.splitlines() if s])  # removes extraneous line breaks
        submission = submission.splitlines()  # Turn submission into a list
        submission = [w.replace('Link: ', '') for w in submission]  # Replace the text 'Link: ' with blankspace. I'd like to do a regex process to fix this sometime, but can't figure it out.
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
        #logdict['object'] = newmap
        #addToMongo(logdict)

    elif message.subject == 'socmedia' and message.author == 'Petrarch1603':
        #TODO add feature to check socmedia messages from here.
        continue

    elif message.subject == 'dayinhistory' and message.author == 'Petrarch1603':
        # TODO add to dayinhistory.db
        DIHmessage = message.body
        DIHmessage = os.linesep.join([s for s in DIHmessage.splitlines() if s])
        DIHmessage = DIHmessage.splitlines()
        dayinhistory = ''
        raw_id = ''
        text = ''
        for item in DIHmessage:
            if isinstance(item, int) and 0 < item < 366:
                dayinhistory = item
            elif item.startswith("https://redd.it/"):
                raw_id = item[-6:]
            else:
                text = item
        if text == '' or raw_id == '' or dayinhistory == '':
            send_reddit_message_to_self(title='Error processing day in history', message=("Cannot parse this "
                                                                                          "message: \n" + DIHmessage))
        else:
            add_to_historydb(raw_id=raw_id, day_of_year=dayinhistory, text=text)
        message.mark_read()

    else:
        msg = message.body
        author = str(message.author)
        subject = message.subject
        r.redditor(my_reddit_ID).message('Message sent to Bot, Please check on it   \n', '*/u/' +
                                                author + '* sent this message to the bot. Please check on it.    \n' +
                                                '**Subject:** ' + subject + '     \n' + '**Message:**   \n' + msg)
        newMessageObject = {'author': author, 'subject': subject, 'body': msg}
        #logdict['object'] = newMessageObject
        #addToMongo(logdict)
        message.mark_read()

