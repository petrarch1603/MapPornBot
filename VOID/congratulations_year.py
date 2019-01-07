'''Congratulations post for best map of the year.'''

import classes
import functions
import os
import praw

# Todo: can this be done as part of the normal congratulations script, that way I don't have to maintain two scripts

# Verify before running in case of accidental execution.
# If this script is automated, this line will need to be deleted.
input('Are you ready?')

r = praw.Reddit('bot1')
log_db = classes.LoggingDB()
cont_db = classes.ContestDB()


def get_raw_id() -> object:
    """Get the raw ID of the voting post.

    :return: PRAW Object
    :rtype: object

    """
    votingpostdata = open('data/votingpostdata.txt', 'r')
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
    voting_post.mod.contest_mode(state=False)

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
    for comment in voting_post.comments:
        score = int(comment.score)
        found_id = id_regex.search(comment.body)  # Find those ID's
        if found_id is None:
            continue
        message_id = str(found_id.group()).replace('^^^^', '')

        for obj in cont_db.current_list:
            if message_id == str(obj.raw_id):
                mapcomment = comment.reply("Map by: " + str(obj.author))
                mapcomment.mod.distinguish(how='yes')
                cont_db.add_vote_count_to_submission(raw_id=message_id, votecount=score)
                yyyymm = int(obj.cont_date)

    n = 0
    winner, win_map_url = '', ''
    for obj in cont_db.get_sorted_top_of_month(month=yyyymm)[:4]:
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
    post_title = ('Congratulations to /u/{}: winner of {}\'s Monthly Map Contest!'.format(winner, contest_month_pretty))
    congrats_submission = r.subreddit('mapporn').submit(post_title, selftext=congrats_data)
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




# # # #
votingpostdata = open('data/votingpostdata.txt', 'r')
raw_id = (votingpostdata.read())
votingPost = r.submission(id=raw_id)
bot_disclaimer_text = bot_disclaimer()
votingPost.mod.sticky(state=False)

# # 2) Prepare a new CSV with the top four maps.
# This will be referenced at the end of the year for the
# Annual map contest of best map of the year.
# # Get some month and year congratsData for the previous month
date_10_days_ago = datetime.now() - timedelta(days=10)
contest_year = str(date_10_days_ago.date().year)
winners_csv = str('BestOf' + contest_year + '.csv')

# # 3) Prepare the loop for parsing contestant maps
# Prepare the text of the post.
# Congratulations_text is a boilerplate template for each month's congratulations post.
# There are a number of variables that need to be changed on this template though.
# We will do that in the for loop.
congratulations_text = open('Congratulations_text.txt', 'r')
congratsData = congratulations_text.read()

# Prepare a regex script to find the unique ID on each comment.
id_regex = re.compile(r'\^\^\^\^\w\w\w\w\w\w')

# # 4) The Loop
# Gets top four highest upvoted comments and iterates thru them doing operations each time.
allSubmissionsList = []
for comment in votingPost.comments:
    singleMapList = []
    score = int(comment.score)
    foundID = id_regex.search(comment.body)  # Find those ID's
    if foundID is None:
        continue
    message_id = str(foundID.group()).replace('^^^^', '')
    singleMapList.append(score)
    singleMapList.append(message_id)
    allSubmissionsList.append(singleMapList)
    with open('SubmissionsArchive/finalists' + contest_year + '.csv') as current_csv:
        csvreader = csv.reader(current_csv)
        for row in csvreader:
            if message_id == row[4]:
                mapcomment = comment.reply("Map by: " + row[3])
                mapcomment.mod.distinguish(how='yes')

sortedWinnerList = sorted(allSubmissionsList, reverse=True, key=lambda x: x[0])

n = 0
allWinnerList = []
for sortedItem in sortedWinnerList[:4]:
    n = n + 1
    winnerList = []
    with open('SubmissionsArchive/finalists' + contest_year + '.csv') as current_csv:
        csvreader = csv.reader(current_csv)
        for row in csvreader:
            if sortedItem[1] == row[4]:
                placemap = row[0]  # Get name of the map
                placeurl = row[1]  # Get URL of the map
                placedesc = row[2]  # Get description of the map
                placeuser = row[3]  # Get user (creator) of the map
    winnerList.append(str(placemap))  # These lines create a list for the top posts of the month csv
    winnerList.append(str(placeurl))
    winnerList.append(str(placedesc))
    winnerList.append(str(placeuser))
    winnerList.append(str(sortedItem[1]))  # Unique ID
    winnerList.append(str(sortedItem[0]))  # Number of votes
    congratsData = str(congratsData)  # congratsData is the Congratulations text template, now we're going to replace variables
    congratsData = congratsData.replace(str('%' + str(n) + 'PLACEUSER%'), str(placeuser))
    congratsData = congratsData.replace(str('%' + str(n) + 'PLACEVOTES%'), str(sortedItem[0]))
    placemap = placemap.replace('Map Name: ', '')
    congratsData = congratsData.replace(str('%' + str(n) + 'PLACEMAP%'), str(placemap))
    congratsData = congratsData.replace(str('%' + str(n) + 'PLACEURL%'), str(placeurl))
    with open('SubmissionsArchive/' + winners_csv, 'a') as winnerFile:
        wr = csv.writer(winnerFile)  # Write the list in a comma delimited format
        wr.writerow(winnerList)

# # 5) Post congratulations post to reddit

# Get the winner in a variable 'winner'
# Seems the easiest way to do this is to just get it from the first line of the CSV that we just created.
with open('SubmissionsArchive/' + winners_csv, 'r') as winnerFile:
    winnerReader = csv.reader(winnerFile)
    winnerReader = list(winnerReader)
    winner = winnerReader[0][3]
    win_map_url = winnerReader[0][1]

# Put the contest post URL into the congratulations template.
congratsData = congratsData.replace('%VOTINGPOSTURL%', votingPost.shortlink)
congratsData = congratsData.replace('%MYUSERID%', my_reddit_ID)
post_title = ('Congratulations to /u/' + winner + ': winner of the best map of ' + contest_year + '!')
congratsSubmission = r.subreddit('mapporn').submit(post_title, selftext=congratsData)  # Submits the post to Reddit
congratulations_text.close()
congrats_shortlink = congratsSubmission.shortlink
congratsSubmission.mod.distinguish()
try:
    congratsSubmission.mod.sticky()
except:
    send_reddit_message_to_self('Error encountered', message=('Could not sticky this post: ' + congrats_shortlink))
    pass

# # 6) Turn contest mode OFF on the original voting post
# Need to do this in order to count the votes, otherwise all posts show 1 vote.
votingPost.mod.contest_mode(state=False)


# # 7) Post congratulations post to social media
# Download the image locally
winningImage = 'temp.jpg'
request = requests.get(win_map_url, stream=True)
if request.status_code == 200:
    with open(winningImage, 'wb') as image:
        for chunk in request:
            image.write(chunk)
    filesize = os.path.getsize('temp.jpg')
    if filesize > 3070000:  # If it's too big social media sites won't like it.
        os.remove(winningImage)
        winningImage = 'misc_images/01.png'  # This is a backup image to post in lieu of the winning map.
else:
    winningImage = 'misc_images/01.png'

# Post to social media.
# Now that we have the image we can run the function to post it to the social media sites
generic_message = generic_post(imagefile=winningImage, message=(post_title + ' ' + congrats_shortlink))

# # 8) Send message to me with shortlinks for QC and social media URLs
message_to_me = ('The new Congratulations post has just posted.    \nThe congrats post is here: ' + congrats_shortlink + '   \n' + 'Verify that the original post has contest mode turned OFF: ' +
                 votingPost.shortlink + '   \n' + generic_message)
send_reddit_message_to_self(title='Congratulation post posted', message=message_to_me)


# # 10) Send message to winner congratulating them
congratsMessage = ('[Congratulations, you won this year\'s Map Contest!](' + congrats_shortlink + ')    \n' + bot_disclaimer_text)
r.redditor(winner).message('Congratulations!', congratsMessage)
