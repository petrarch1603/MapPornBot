"""Script for creating a voting post for best maps of the year."""

import classes
from datetime import datetime, timedelta
import fnmatch
import functions
import GridCollage
import os
import praw
import sys
import random
import urllib.request

dryrun = True

if dryrun is False:
    subreddit = 'mapporn'
else:
    subreddit = 'mappornsandbox'


def prepare_voting_text() -> str:
    """Prepares the self text for the voting post

    :return: text of voting post
    :rtype: str

    """
    with open('data/year_end_votingtext.txt', 'r') as my_file:
        year_voting_text = my_file.read()
    next_sunday = functions.next_weekday(datetime.now(), 6)
    next_sunday = next_sunday.strftime('%A %B %d, %Y')
    numbersubmitted = len(finalists_list)
    year_voting_text = year_voting_text.replace('%NUMBERSUBMITTED%', str(numbersubmitted))
    year_voting_text = year_voting_text.replace('%ENDDATE%', str(next_sunday))
    year_voting_text = year_voting_text.replace('%MYREDDITID%', functions.my_reddit_ID)
    return year_voting_text


def main() -> str:
    """Main script to run voting post

    :returns: shortlink to voint post
    :rtype: str

    """
    error_message = ''
    year_voting_text = prepare_voting_text()
    submission = r.subreddit(subreddit).submit(post_message, selftext=year_voting_text)  # Submits the post to Reddit
    submission.mod.contest_mode()
    submission.mod.distinguish()
    shortlink = submission.shortlink
    functions.send_reddit_message_to_self(title='Reminder', message='[Remember to request Reddit Gold]'
                                                                    '(https://redd.it/a335e1)    +\n/r/MapPorn '
                                                                    '/u/Petrarch1603 ' + shortlink)
    title_to_finalist = 'The Annual Best Map of the Year contest is now live!'
    message_to_finalist = ('**The Annual Best Map of the Year contest is now live!**    \nThank you for contributing a '
                           'map. [The voting on the contest is open now at this link.](' + shortlink + ')    \n' +
                           bot_disclaimer_text)

    authors_list = []
    for map_row in finalists_list:
        submission.reply('[' + str(map_row.map_name) + '](' + str(map_row.url) + ')   \n'
                         '' + str(map_row.desc) + '\n\n----\n\n^^^^' + str(map_row.raw_id))
        authors_list.append(map_row.author)

    authors_list = set(authors_list)  # This will remove duplicate names from the authors list
    if dryrun is False:
        for author in authors_list:
            try:
                r.redditor(author).message(title_to_finalist, message_to_finalist)
            except Exception as e:
                error_message += 'Error sending message to ' + author + '   \n' + str(e)
    generalcomment = submission.reply('General Comment Thread')
    generalcomment.mod.distinguish(sticky=True)
    generalcomment.reply('**What is with the ^^^small characters?**    \nThis contest is automated with a bot. The bot '
                         'uses these random characters to index the maps and to calculate the winner at the end of the '
                         'contest.\n\n----\n\n ^^^[Github](https://github.com/petrarch1603/MapPornBot)')
    if error_message != '':
        functions.send_reddit_message_to_self(title="error", message=error_message)
    submission.mod.approve()  # Unsure if these two work
    submission.mod.sticky()
    return shortlink


def post_advertisement_to_soc_media(shortlink: str, image_file_name: str = '') -> str:
    """Advertises the voting contest on social media


    :param image_file_name: path to image that is to be posted to social media, default is none.
    :type image_file_name: str

    :param shortlink: shortlink to Reddit contest
    :type shortlink: str

    :return: URL to advertisement Tweet
    :rtype: str

    """
    error_message = ''
    post_message_with_url = (post_message + '\n' + shortlink + '\n#MapPorn #Cartography #Contest')

    if image_file_name == '':
        # Get random image_file_name from the directory of vote images.
        imagecount = len([name for name in os.listdir('voteimages/')])  # counts how many images are in the directory
        randraw = random.randint(1, imagecount)  # Creates a random number between 1 and the image count.

        # Return a random number with a leading zero if necessary. (i.e. 02 instead of 2)
        image_file_name = str(randraw).zfill(2)

        # Look in the directory and create a list of files with the name of the image.
        image_file_name = fnmatch.filter(os.listdir('voteimages/'), image_file_name + '.*')
        image_file_name = image_file_name[0]

        # Post to social media
        image_file_name = ('voteimages/' + image_file_name)
    try:
        social_media_post = classes.GenericPost(filename=image_file_name, title=post_message_with_url)
        socialmediadict = social_media_post.post_to_all_social()
        functions.send_reddit_message_to_self('New Voting Post Posted',
                                              'A new votingpost.py has been run. Check the post to make'
                                              ' sure the bot did it right.   \nHere\'s the link to the '
                                              'post: ' + shortlink + '   \nHere\'s the social media '
                                              'links:    \n' + str(socialmediadict['tweet_url']))
        return str(socialmediadict['tweet_url'])
    except Exception as e:
        error_message += "Could not post results to social media.   \n{}    \n\n".format(str(e))
    if error_message != '':
        functions.send_reddit_message_to_self(title="error", message=error_message)


if __name__ == "__main__":
    bot_disclaimer_text = functions.bot_disclaimer()
    contest_year = (datetime.now() - timedelta(days=10)).year
    cont_db = classes.ContestDB()
    finalists_list = cont_db.get_top_posts_of_year()

    # Verify that all the finalist maps have valid URLs:
    for obj in finalists_list:
        if urllib.request.urlopen(obj.url).getcode() != 200:
            finalists_list.remove(obj)

    post_message = 'Vote Now for the best map of ' + str(contest_year) + '!'
    r = praw.Reddit('bot1')
    shortlink = main()
    print(shortlink)

    # Create Grid Collage
    my_urls = []
    for i in finalists_list:
        my_urls.append(i.url)
    collage_filepath: str = GridCollage.create_grid(url_list=my_urls, text_content="Best of " + str(contest_year))

    if dryrun is False:
        print(post_advertisement_to_soc_media(shortlink=shortlink, image_file_name=collage_filepath))
    else:
        print(collage_filepath)
