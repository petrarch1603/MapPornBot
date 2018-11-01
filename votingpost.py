from classes import *
import csv
import fnmatch
from functions import *
import os
import praw

r = praw.Reddit('bot1')


# Verify before running in case of accidental execution.
# If this script is automated, this line will need to be deleted.
input('Are you ready?')

# # 1) Prepare the self text of the voting post
botDisclaimerText = bot_disclaimer()

# Include the number of submissions and the contest end date in the text of the post.
# This code makes the end date next Sunday.


def prepare_voting_text():
    with open('VotingText.txt', 'r') as my_file:
        my_voting_text = my_file.read()
    lastmonthfile = open('data/lastmonth.txt', 'r')
    last_month_url = (lastmonthfile.read())
    next_week = datetime.now() + timedelta(days=5)  # Need at least 5 days to vote.
    next_sunday = next_weekday(next_week, 6)  # Pycharm doesn't like the .now(), but in testing seems it should work.
    pretty_next_sunday = next_sunday.strftime('%A %B %d, %Y')
    numbersubmitted = sum(1 for _ in open('submissions.csv'))
    my_voting_text = my_voting_text.replace('%NUMBERSUBMITTED%', str(numbersubmitted))
    my_voting_text = my_voting_text.replace('%ENDDATE%', str(pretty_next_sunday))
    my_voting_text = my_voting_text.replace('%MYREDDITID%', my_reddit_ID)
    my_voting_text = my_voting_text.replace('%LASTMONTH%', last_month_url)
    return my_voting_text


def main():
    error_message = ''
    voting_text = prepare_voting_text()
    date_7_days_ago = datetime.now() - timedelta(days=7)
    contest_month = date_7_days_ago.strftime("%B")
    contest_year = date_7_days_ago.date().year

    post_message = 'Vote Now for the ' + str(contest_month) + ' ' + str(contest_year) + ' Map Contest!'
    submission = r.subreddit('mapporn').submit(post_message, selftext=voting_text)  # Submits the post to Reddit
    submission.mod.contest_mode()
    submission.mod.distinguish()
    shortlink = submission.shortlink

    with open('submissions.csv', 'r') as f:
        reader = csv.reader(f)
    for row in reader:
        submission.reply('[' + row[0] + '](' + row[1] + ')   \n' + row[2] + '\n\n----\n\n^^^^' + row[4])
        # the brackets and parentheses are for hyperlinking the name, row[4] is the unique ID of the submission message,
        # in the congratulations.py program the bot will parse these comments looking for this code and use it to
        # determine the winners.

        # Now send a message to each contestant letting them know it's live.
        try:
            r.redditor(row[3]).message('The monthly map contest is live!', 'Thank you for contributing a map. '
                                                                           '[The voting on the monthly contest is '
                                                                           'open now at this link.]('
                                                                           + shortlink + ')    \n' + botDisclaimerText)
        except Exception as e:
            print('Could not send message to ' + row[3] + '   \n' + str(e))

    # General Comment Thread so people don't post top level comments
    generalcomment = submission.reply('General Comment Thread')
    generalcomment.mod.distinguish(sticky=True)
    generalcomment.reply('**What is with the ^^^small characters?**    \n'
                         'This contest is automated with a bot. The bot uses these random characters to index the maps '
                         'and to calculate the winner at the end of the contest.\n\n----\n\n'
                         '^^^[Github](https://github.com/petrarch1603/MapPornBot)')

    # # Need to save the voting post raw_id for use in parsing the winner after a few days.
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

    imagecount = len([name for name in os.listdir('voteimages/')])  # counts how many images are in the directory
    randraw = random.randint(1, imagecount)  # Creates a random number between 1 and the image count.
    # Return a random number with a leading zero if necessary. (i.e. 02 instead of 2)
    image_file_name = str(randraw).zfill(2)
    # Look in the directory and create a list of files with the name of the image.
    #
    # It's not elegant code, but it returns a full file name (i.e. 02.png instead of 02).
    # The problem is that there are multiple file exensions: jpg, png, jpeg, etc.
    # There is probably a better way to do it, but for now it works.
    image_file_name = fnmatch.filter(os.listdir('voteimages/'), image_file_name + '.*')
    image_file_name = image_file_name[0]    # There should only be one image with that name, so this returns the name of

    # Post to social media
    # Change the message so it includes URL of the Reddit voting post.
    post_message_url = (post_message + '\n' + shortlink + '\n#MapPorn #Cartography #Contest')
    image_file_name = ('voteimages/' + image_file_name)

    # Run a function to post it to different social media accounts
    try:
        social_media_post = GenericPost(filename=image_file_name, title=post_message_url)
        socialmediadict = social_media_post.post_to_all_social()
        send_reddit_message_to_self('New Voting Post Posted', 'A new votingpost.py has been run. Check the post to make '
                                                              'sure the bot did it right.   \nHere\'s the link to the '
                                                              'post: ' + shortlink + '   \nHere\'s the social media '
                                                              'links:    \n' + str(socialmediadict['tweet_url']))
    except Exception as e:
        error_message += "Could not post results to social media.   \n{}    \n\n".format(str(e))

    try:
        submission.mod.approve()  # Unsure if these two work
    except Exception as e:
        print('Could not approve post. Exception: ' + str(e))
    try:
        submission.mod.sticky()
    except Exception as e:
        print('Could not sticky post. Exception: ' + str(e))


if __name__ == "__main__":
    main()

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
