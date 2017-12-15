from functions import *


# Verify before running in case of accidental execution.
# If this script is automated, this line will need to be deleted.
input('Are you ready?')

# # 1) Prepare the self text of the voting post
VotingText = open('VotingText.txt', 'r').read()
botDisclaimerText = bot_disclaimer()

# Include the number of submissions and the contest end date in the text of the post.
# This code makes the end date next Sunday.

lastmonthfile = open('data/lastmonth.txt', 'r')
last_month_url = (lastmonthfile.read())
next_sunday = next_weekday(datetime.now(), 6)  # Pycharm doesn't like the .now(), but in testing seems it should work.
next_sunday = next_sunday.strftime('%A %B %d, %Y')
numbersubmitted = sum(1 for line in open('submissions.csv'))
VotingText = VotingText.replace('%NUMBERSUBMITTED%', str(numbersubmitted))
VotingText = VotingText.replace('%ENDDATE%', str(next_sunday))
VotingText = VotingText.replace('%MYREDDITID%', my_reddit_ID)
VotingText = VotingText.replace('%LASTMONTH%', last_month_url)

# # 2) Get date from 7 days ago
# We need to get the month from the previous month. Most of the contests are towards the end of the month.
# Sometimes the voting is even in the first few days of the next month.
# Therefore we need to get the date from 7 days earlier. That will be the month for the intent of the title of the
# Reddit post.
date_7_days_ago = datetime.now() - timedelta(days=7)
contest_month = date_7_days_ago.strftime("%B")
contest_year = date_7_days_ago.date().year

# # 3) Submit the post to Reddit
post_message = 'Vote Now for the ' + str(contest_month) + ' ' + str(contest_year) + ' Map Contest!'
submission = r.subreddit('mapporn').submit(post_message, selftext=VotingText)  # Submits the post to Reddit
submission.mod.contest_mode()
submission.mod.distinguish()
shortlink = submission.shortlink

# # 4) One by one add a comment to the post, each comment being a map to vote on
f = open('submissions.csv', 'r')
reader = csv.reader(f)
for row in reader:
    submission.reply('[' + row[0] + '](' + row[1] + ')   \n' + row[2] + '\n\n----\n\n^^^^' + row[4])
    # the brackets and parentheses are for hyperlinking the name, row[4] is the unique ID of the submission message,
    # in the congratulations.py program the bot will parse these comments looking for this code and use it to determine
    # the winners.

    # Now send a message to each contestant letting them know it's live.
    r.redditor(row[3]).message('The monthly map contest is live!', 'Thank you for contributing a map. '
                                                                   '[The voting on the monthly contest is '
                                                                   'open now at this link.]('
                               + shortlink + ')    \n' + botDisclaimerText)
generalcomment = submission.reply('General Comment Thread')  # Have a general comment thread so
                                                             # people don't post top level comments.
generalcomment.mod.distinguish(sticky=True)
generalcomment.reply('**What is with the ^^^small characters?**    \n'
                     'This contest is automated with a bot. The bot uses these random characters to index the maps and '
                     'to calculate the winner at the end of the contest.\n\n----\n\n ^^^[Github](https://github.com/petrarch1603/MapPornBot)')
f.close()


# # 5) Need to save the voting post raw_id for use in parsing the winner after a few days.
raw_id = submission.id_from_url(shortlink)
file = open('data/votingpostdata.txt', 'w')
file.write(raw_id)
file.close()

# # 6) Rename submissions to submissions_current (while there is voting going on).

# SubmissionsCurrent will be the index of what is being voted on during the voting period. That way after the vote
# we know who is the winner.
os.replace('submissions.csv', 'submissions_current.csv')
# Create a new submissions.csv, so that if we get submissions during the contest, they will be acquired without
# creating conflicts. This code creates an empty file.
open('submissions.csv', 'w').close()

# # 7) Need to post a "Vote Now' advertisement to social media
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
# The function returns a text string with the URLs of the relevant social media posts.
# This is useful for verifying proper posting.


# # 8) Send a Reddit message to me with a summary and links to social media posts
send_reddit_message_to_self('New Voting Post Posted', 'A new votingpost.py has been run. Check the post to make sure the bot did it right.'
                                   '   \nHere\'s the link to the post: ' + shortlink + '   \nHere\'s the social media '
                                                                                       'links:    \n' + socialmedialinks)

submission.mod.approve()  # Unsure if these two work
submission.mod.sticky()


# # Notes
#
#   2017/12/02
#       Mostly successful execution. Social media post failed due to not having the images ready.
#       Fixed this for next time. I'm still unsure if the submission.mod.approve() and
#       submission.mod.sticky() functions will work. Will have to check that next month.
#
#       Also next time, make sure that the submissions.csv is renamed to submissions_current.
#       Make a copy of submissions.csv before executing script next time!
#
#