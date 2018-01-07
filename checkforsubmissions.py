import os
import praw
import csv
from functions import my_reddit_ID, bot_disclaimer, SubmissionObject
import datetime
import time
import json

# Print time and date for verification
print(datetime.datetime.now())

r = praw.Reddit('bot1')
disclaimer = bot_disclaimer()
MessageReply = 'Your map has been received.   ' + '\n' + 'Look for the voting post for the contest soon.    ' + '\n' + \
               '&nbsp;       ' + '\n' + disclaimer
                # To Do: add contest date to the MessageReply, that way users know when the contest is.

logdict = {}
newMessage = 'false'

for message in r.inbox.unread():
    # noinspection PyRedeclaration
    newMessage = 'true'

if newMessage is 'false':
    logdict['time'] = time.time()
    logdict['type'] = 'inbox check'
    logdict['status'] = 'noChange'
    with open('data/progressLog.json', 'a') as outfile:
        json.dump(logdict, outfile)

for message in r.inbox.unread():
    if message.subject == "Map Contest Submission":
        logdict['status'] = 'contestSubmission'
        logdict['time'] = time.time()
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
                                                                       'Check the CSV for formatting')
        message.mark_read()
        logdict['object'] = newmap.__dict__
        try:
            print(str(newmap.unique_message))
        except:
            pass

        with open('data/progressLog.json', 'a') as outfile:
            json.dump(logdict, outfile)

    else:
        logdict['status'] = 'messageToBot'
        msg = message.body
        author = str(message.author)
        subject = message.subject
        r.redditor(my_reddit_ID).message('Message sent to Bot, Please check on it   \n', '*/u/' +
                                                author + '* sent this message to the bot. Please check on it.    \n' +
                                                '**Subject:** ' + subject + '     \n' + '**Message:**   \n' + msg)
        newMessageObject = {'author': author, 'subject': subject, 'body': msg}
        logdict['object'] = newMessageObject
        with open('data/progressLog.json', 'a') as outfile:
            json.dump(logdict, outfile)
        message.mark_read()

