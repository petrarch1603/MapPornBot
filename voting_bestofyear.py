import csv
import os
import fnmatch
from datetime import datetime, timedelta
from functions import *

input('Are you ready?')

contest_year = (datetime.now() - timedelta(days=10)).year

## REMOVE HASHTAGS AFTER 2017 CONTEST GOES LIVE
# Create CSV with all final contestants from current year
finalistsCSV = "./SubmissionsArchive/finalists" + str(contest_year) + ".csv"
# finalists = open(finalistsCSV, "a")
# submdir = './SubmissionsArchive'
# for filename in os.listdir(submdir):
#     if fnmatch.fnmatch(filename, '2017*.csv'):
#         print(filename)
#         f = open(submdir + "/" + filename)
#         for line in f:
#             finalists.write(line)
#         f.close()
# finalists.close()

# # Prepare the self text of the voting post
YearVotingText = open('data/year_end_votingtext.txt', 'r').read()
botDisclaimerText = bot_disclaimer()

# Include the number of submissions and the contest end date in the text of the post.
# This code makes the end date next Sunday.

next_sunday = next_weekday(datetime.now(), 6)  # Pycharm doesn't like the .now(), but in testing seems it should work.
next_sunday = next_sunday.strftime('%A %B %d, %Y')
numbersubmitted = sum(1 for line in open(finalistsCSV))
YearVotingText = YearVotingText.replace('%NUMBERSUBMITTED%', str(numbersubmitted))
YearVotingText = YearVotingText.replace('%ENDDATE%', str(next_sunday))
YearVotingText = YearVotingText.replace('%MYREDDITID%', my_reddit_ID)


# # Submit the post to Reddit
post_message = 'Vote Now for the best map of ' + str(contest_year) + '!'
submission = r.subreddit('mapporn').submit(post_message, selftext=YearVotingText)  # Submits the post to Reddit
submission.mod.contest_mode()
submission.mod.distinguish()
shortlink = submission.shortlink
send_reddit_message_to_self(title='Reminder', message='[Remember to request Reddit Gold](https://redd.it/7gqgak)    +\n/r/MapPorn /u/Petrarch1603 ' + shortlink)

# # One by one add a comment to the post, each comment being a map to vote on
f = open(finalistsCSV, 'r')
reader = csv.reader(f)
title_to_finalist = 'The Annual Best Map of the Year contest is now live!'
message_to_finalist = ('**The Annual Best Map of the Year contest is now live!**    \nThank you for contributing a map. [The voting on the contest is open now at this link.]('
                               + shortlink + ')    \n' + botDisclaimerText)
for row in reader:
    submission.reply('[' + row[0] + '](' + row[1] + ')   \n' + row[2] + '\n\n----\n\n^^^^' + row[4])
    # the brackets and parentheses are for hyperlinking the name, row[4] is the unique ID of the submission message,
    # in the congratulations.py program the bot will parse these comments looking for this code and use it to determine
    # the winners.

    # Now send a message to each contestant letting them know it's live.
    print(str(row[3]))
    #r.redditor(row[3]).message(title_to_finalist, message_to_finalist)
for row in reader:
    r.redditor(row[3]).message(title_to_finalist, message_to_finalist)
generalcomment = submission.reply('General Comment Thread')  # Have a general comment thread so
                                                             # people don't post top level comments.
generalcomment.mod.distinguish(sticky=True)
generalcomment.reply('**What is with the ^^^small characters?**    \n'
                     'This contest is automated with a bot. The bot uses these random characters to index the maps and '
                     'to calculate the winner at the end of the contest.\n\n----\n\n ^^^[Github](https://github.com/petrarch1603/MapPornBot)')
f.close()


# # Need to save the voting post raw_id for use in parsing the winner after a few days.
raw_id = submission.id_from_url(shortlink)
file = open('data/votingpostdata.txt', 'w')
file.write(raw_id)
file.close()


# # Need to post a "Vote Now' advertisement to social media
# I created a bunch of "Vote Now" posters for use in social media posts.
# They are all in the 'voteimages' directory and have simple two digit file names: 01.png, 02.png, 03.png etc.
# Each month a random image will be posted to social media.

# Get random image_file_name
imagecount = len([name for name in os.listdir('voteimages/')]) # counts how many images are in the directory
randraw = random.randint(1, imagecount)  # Creates a random number between 1 and the image count.
# Return a random number with a leading zero if necessary. (i.e. 02 instead of 2)
image_file_name = str(randraw).zfill(2)
# Look in the directory and create a list of files with the name of the image.
#
# It's not elegant code, but it returns a full file name (i.e. 02.png instead of 02).
# The problem is that there are multiple file exensions: jpg, png, jpeg, etc.
# There is probably a better way to do it, but for now it works.
image_file_name = fnmatch.filter(os.listdir('voteimages/'), image_file_name + '.*')
image_file_name = image_file_name[0]  # There should only be one image with that name, so this returns the name of that file.

# Post to social media
# Change the message so it includes URL of the Reddit voting post.
post_message_url = (post_message + '\n' + shortlink + '\n#MapPorn #Cartography #Contest')
image_file_name = ('voteimages/' + image_file_name)

# Run a function to post it to different social media accounts
socialmedialinks = generic_post(image_file_name, post_message_url)

# # Send a Reddit message to me with a summary and links to social media posts
send_reddit_message_to_self(title_to_finalist, (message_to_finalist + '\nSocMed links: ' + socialmedialinks))

submission.mod.approve()  # Unsure if these two work
submission.mod.sticky()


