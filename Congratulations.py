"""Script to get the results of the Map Contest on /r/MapPorn and congratulate the winner"""

import classes
from datetime import datetime, timedelta
import functions
import os
import praw
import re
import requests
import sys

subreddit = 'mapporn'

r = praw.Reddit('bot1')
log_db = classes.LoggingDB()
cont_db = classes.ContestDB()

date_10_days_ago = datetime.now() - timedelta(days=10)


if len(sys.argv) > 1 and sys.argv[1] == 'year':
    end_of_year = True
    finalists_list = cont_db.get_top_posts_of_year()
    contest_month_pretty = "Best of " + str(date_10_days_ago.year)
    votingpostdata = open('data/votingpostdata.txt', 'r')
elif len(sys.argv) == 1:
    end_of_year = False
    finalists_list = cont_db.current_list
    contest_month_pretty = str(date_10_days_ago.strftime("%B")) + "\'s Monthly"
    votingpostdata = open('data/votingpostdata.txt', 'r')
else:
    functions.send_reddit_message_to_self(title="error in script", message="illegal number of sysargv's ")
    exit()


def get_raw_id() -> object:
    """Get the raw ID of the voting post.

    :return: PRAW Object
    :rtype: object

    """
    raw_id = (votingpostdata.read())
    return r.submission(id=raw_id)


def main():
    """Main Script for posting congratulations."""
    my_diag = classes.Diagnostic(script=str(os.path.basename(__file__)))
    voting_post = get_raw_id()
    my_diag.raw_id = voting_post.id
    my_diag.title = "Contest Congratulations"
    bot_disclaimer_text = functions.bot_disclaimer()
    voting_post.mod.sticky(state=False)
    # # Turn contest mode OFF on the original voting post
    # Need to do this in order to count the votes, otherwise all posts show 1 vote.
    try:
        voting_post.mod.contest_mode(state=False)
    except Exception:
        functions.send_reddit_message_to_self(title="could not turn off contest mode",
                                              message="turn it off here:" + str(voting_post.url))

    # Prepare the loop for parsing contestant maps
    # Prepare the text of the post.
    # Congratulations_text is a boilerplate template for each month's congratulations post.
    # There are a number of variables that need to be changed on this template though.
    # We will do that in the for loop.
    with open('Congratulations_text.txt', 'r') as f:
        congrats_data = str(f.read())

    # Prepare a regex script to find the unique ID on each comment.
    id_regex = re.compile(r'\^\^\^\^\w\w\w\w\w\w')

    # # The Loop
    # Gets top four highest upvoted comments and iterates thru them doing operations each time.
    yyyymm = 0
    winning_objects_list = []
    for comment in voting_post.comments:
        my_score = int(comment.score)
        print(my_score)
        found_id = id_regex.search(comment.body)  # Find those ID's
        if found_id is None:
            continue
        message_id = str(found_id.group()).replace('^^^^', '')

        for obj in finalists_list:
            map_row_list = []
            if message_id == str(obj.raw_id):
                mapcomment = comment.reply("Map by: " + str(obj.author))
                mapcomment.mod.distinguish(how='yes')
                if end_of_year is True:
                    # The order of this list is important, do not rearrange!
                    map_row_list.append(str(obj.map_name))
                    map_row_list.append(str(obj.url))
                    map_row_list.append('')
                    map_row_list.append(str(obj.author))
                    map_row_list.append('')
                    map_row_list.append(my_score)
                    my_map_row_obj = classes.MapRow(schema=cont_db.schema, table=cont_db.table, row=map_row_list)
                    winning_objects_list.append(my_map_row_obj)
                else:
                    cont_db.add_vote_count_to_submission(raw_id=message_id, votecount=my_score)
                    yyyymm = int(obj.cont_date)
    winner, win_map_url = '', ''
    if end_of_year is False:
        winning_objects_list = cont_db.get_sorted_top_of_month(month=yyyymm)
    else:
        winning_objects_list.sort(key=lambda x: x.votes, reverse=True)
        assert len(winning_objects_list) == len(cont_db.get_top_posts_of_year())

    assert winning_objects_list[0].votes >= winning_objects_list[2].votes

    n = 0
    for obj in winning_objects_list[:4]:
        n += 1
        if n == 1:
            winner = obj.author
            win_map_url = obj.url
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEUSER%'), str(obj.author))
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEVOTES%'), str(obj.votes))
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEMAP%'), str(obj.map_name))
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEURL%'), str(obj.url))
    # # Post congratulations post to reddit


# Put the contest post URL into the congratulations template.
    congrats_data = congrats_data.replace('%VOTINGPOSTURL%', voting_post.shortlink)
    congrats_data = congrats_data.replace('%MYUSERID%', functions.my_reddit_ID)
    post_title = ('Congratulations to /u/{}: winner of {} Map Contest!'.format(winner, contest_month_pretty))
    congrats_submission = r.subreddit(subreddit).submit(post_title, selftext=congrats_data)
    congrats_shortlink = congrats_submission.shortlink
    congrats_submission.mod.distinguish()
    try:
        congrats_submission.mod.approve()
        congrats_submission.mod.sticky()
    except Exception as e:
        functions.send_reddit_message_to_self(title='Error encountered',
                                              message=('Could not sticky this post: {}    \n{}    \n\n'
                                                       .format(congrats_shortlink, str(e))))

    # # Post congratulations post to social media
    # Download the image locally
    winning_image = 'temp.jpg'
    request = requests.get(win_map_url, stream=True)
    if request.status_code == 200:
        with open(winning_image, 'wb') as image:
            for chunk in request:
                image.write(chunk)
        filesize = os.path.getsize('temp.jpg')
        if filesize > 3070000:  # If it's too big social media sites won't like it.
            os.remove(winning_image)
            winning_image = 'misc_images/01.png'  # This is a backup image to post in lieu of the winning map.
    else:
        winning_image = 'misc_images/01.png'
    # Post to social media.
    # Now that we have the image we can run the function to post it to the social media sites
    try:
        generic_post = classes.GenericPost(filename=winning_image, title=(post_title + ' ' + congrats_shortlink))
        social_media_dict = generic_post.post_to_all_social()
        functions.send_reddit_message_to_self(title='The new Congratulations post has just posted.',
                                              message='The congrats post is here:    {}\n    \n{}    \n{}')\
            .format(str(congrats_shortlink), str(voting_post.shortlink), str(social_media_dict['tweet_url']))
    except Exception as e:
        functions.send_reddit_message_to_self(title='Could not post to social media',
                                              message='Could not post announcement to socialmeda:    \n{}    \n\n'
                                              .format(str(e)))

    # # Send message to winner congratulating them
    congrats_message = ('[Congratulations, you won this month\'s Map Contest!](' + congrats_shortlink + ')    \n' +
                        bot_disclaimer_text)
    try:
        r.redditor(winner).message('Congratulations', congrats_message)
    except Exception as e:
        functions.send_reddit_message_to_self(title='Could not send message to winner',
                                              message='Error: {}'.format(str(e)))
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)


if __name__ == "__main__":
    main()
