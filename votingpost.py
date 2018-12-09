"""Script for creating a voting post for a new /r/MapPorn Map Contest"""

from datetime import datetime, timedelta
import classes
import functions
import praw

r = praw.Reddit('bot1')
cont_db = classes.ContestDB()
numbersubmitted = cont_db.live_count
botDisclaimerText = functions.bot_disclaimer()


def prepare_voting_text():
    """Prepares the Voting Post Self Text with information populated.

    :return: Voting Post text with information filled out.
    :rtype: str

    """

    with open('VotingText.txt', 'r') as my_file:
        my_voting_text = my_file.read()
    lastmonthfile = open('data/lastmonth.txt', 'r')
    last_month_url = (lastmonthfile.read())
    next_week = datetime.now() + timedelta(days=5)  # Need at least 5 days to vote.
    next_sunday = functions.next_weekday(next_week, 6)
    pretty_next_sunday = next_sunday.strftime('%A %B %d, %Y')
    my_voting_text = my_voting_text.replace('%NUMBERSUBMITTED%', str(numbersubmitted))
    my_voting_text = my_voting_text.replace('%ENDDATE%', str(pretty_next_sunday))
    my_voting_text = my_voting_text.replace('%MYREDDITID%', functions.my_reddit_ID)
    my_voting_text = my_voting_text.replace('%LASTMONTH%', last_month_url)
    return my_voting_text


def main():
    """Main script to prepare and post voting post for Map Contest"""
    error_message = ''
    voting_text = prepare_voting_text()
    date_7_days_ago = datetime.now() - timedelta(days=7)
    contest_month = date_7_days_ago.strftime("%B")
    contest_year = date_7_days_ago.date().year
    month_year = (str(contest_month) + ' ' + str(contest_year))
    post_message = ('Vote Now for the ' + month_year + ' Map Contest!')
    yyyymm = int(str(contest_year) + str(date_7_days_ago.strftime("%m")))

    submission = r.subreddit('mapporn').submit(post_message, selftext=voting_text)  # Submits the post to Reddit
    submission.mod.contest_mode()
    submission.mod.distinguish()
    shortlink = submission.shortlink

    my_urls_list = []  # List of urls of all maps being submitted, used to make grid collage

    # Post each map as a comment
    for obj in cont_db.live_list:
        submission.reply('[' + str(obj.map_name) + '](' + str(obj.url) + ')   \n'
                         '' + str(obj.desc) + '\n\n----\n\n^^^^' + str(obj.raw_id))

        # Send a message to each contestant letting them know it's live.
        try:
            r.redditor(obj.author).message('The monthly map contest is live!',
                                           'Thank you for contributing a map. '
                                           '[The voting on the monthly contest is '
                                           'open now at this link.](' + shortlink + ')    \n' + botDisclaimerText)
        except praw.exceptions.APIException as e:
            print('Could not send message to ' + obj.author + '   \n' + str(e))
        try:
            cont_db.add_date_to_submission(raw_id=obj.raw_id, yearmonth=yyyymm)
        except Exception as e:
            functions.send_reddit_message_to_self(title='Voting post error',
                                                  message="could not add contest date "
                                                          "to {}\n    {}".format(obj.raw_id, e))
        my_urls_list.append(obj.url)  # Add URL to list for getting the grid collage

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

    # Advertise Contest on Social Media
    functions.advertise_on_socmedia(list_of_urls=my_urls_list, month_year=month_year, voting_url=shortlink)

    try:
        submission.mod.approve()
    except Exception as e:
        print('Could not approve post. Exception: ' + str(e))
    try:
        submission.mod.sticky()
    except Exception as e:
        print('Could not sticky post. Exception: ' + str(e))
    print(error_message)

    try:
        cont_db.close()
        refreshed_cont_db = classes.ContestDB()
        assert refreshed_cont_db.current_count == numbersubmitted
    except AssertionError:
        functions.send_reddit_message_to_self(title="Error with current count",
                                              message="The current count in the ContestDB does not equal the number of"
                                                      "maps being voted on.")


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
