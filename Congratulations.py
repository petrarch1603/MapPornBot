from functions import *
from classes import LoggingDB, Diagnostic

r = praw.Reddit('bot1')
log_db = LoggingDB()


def get_raw_id():  # # Get the raw ID of the voting post.
    votingpostdata = open('data/votingpostdata.txt', 'r')
    raw_id = (votingpostdata.read())
    return r.submission(id=raw_id)


def main():
    my_diag = Diagnostic(script=str(os.path.basename(__file__)))
    voting_post = get_raw_id()
    my_diag.raw_id = voting_post.id
    my_diag.title = "Contest Congratulations"
    bot_disclaimer_text = bot_disclaimer()
    voting_post.mod.sticky(state=False)

    # # Prepare a new CSV with the top four maps.
    # This will be referenced at the end of the year for the
    # Annual map contest of best map of the year.
    # # Get some month and year congrats_data for the previous month
    date_10_days_ago = datetime.now() - timedelta(days=10)
    contest_month = str(date_10_days_ago.strftime("%m"))
    contest_month_pretty = str(date_10_days_ago.strftime("%B"))
    contest_year = str(date_10_days_ago.date().year)
    winners_csv = str(contest_year + contest_month + 'WINNERS.csv')

    # # 3) Prepare the loop for parsing contestant maps
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
    all_submissions_list = []
    for comment in voting_post.comments:
        single_map_list = []
        score = int(comment.score)
        found_id = id_regex.search(comment.body)  # Find those ID's
        if found_id is None:
            continue
        message_id = str(found_id.group()).replace('^^^^', '')
        single_map_list.append(score)
        single_map_list.append(message_id)
        all_submissions_list.append(single_map_list)
        with open('submissions_current.csv') as current_csv:  # Add reply in voting post with name of map creator
            csvreader = csv.reader(current_csv)
            for row in csvreader:
                if message_id == row[4]:
                    mapcomment = comment.reply("Map by: " + row[3])
                    mapcomment.mod.distinguish(how='yes')

    sorted_winner_list = sorted(all_submissions_list, reverse=True, key=lambda x: x[0])

    n = 0
    for sorted_item in sorted_winner_list[:4]:
        n = n + 1
        winner_list = []
        with open('submissions_current.csv') as current_csv:
            csvreader = csv.reader(current_csv)
            for row in csvreader:
                if sorted_item[1] == row[4]:
                    placemap = str(row[0])  # Get name of the map
                    placeurl = str(row[1])  # Get URL of the map
                    placedesc = str(row[2])  # Get description of the map
                    placeuser = str(row[3])  # Get user (creator) of the map
        winner_list.extend((
            placemap,
            placeurl,
            placedesc,
            placeuser,
            str(sorted_item[1]),
            str(sorted_item[0])
        ))
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEUSER%'), str(placeuser))
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEVOTES%'), str(sorted_item[0]))
        placemap = placemap.replace('Map Name: ', '')
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEMAP%'), str(placemap))
        congrats_data = congrats_data.replace(str('%' + str(n) + 'PLACEURL%'), str(placeurl))
        with open('SubmissionsArchive/' + winners_csv, 'a') as winner_file:
            wr = csv.writer(winner_file)  # Write the list in a comma delimited format
            wr.writerow(winner_list)

    # # Post congratulations post to reddit

    # Get the winner in a variable 'winner'
    # Seems the easiest way to do this is to just get it from the first line of the CSV that we just created.
    with open('SubmissionsArchive/' + winners_csv, 'r') as winner_file:
        winner_reader = csv.reader(winner_file)
        winner_reader = list(winner_reader)
        winner = winner_reader[0][3]
        win_map_url = winner_reader[0][1]

# Put the contest post URL into the congratulations template.
    congrats_data = congrats_data.replace('%VOTINGPOSTURL%', voting_post.shortlink)
    congrats_data = congrats_data.replace('%MYUSERID%', my_reddit_ID)
    post_title = ('Congratulations to /u/{}: winner of {}\'s Monthly Map Contest!'.format(winner, contest_month_pretty))
    congrats_submission = r.subreddit('mapporn').submit(post_title, selftext=congrats_data)
    congrats_shortlink = congrats_submission.shortlink
    congrats_submission.mod.distinguish()
    try:
        congrats_submission.mod.approve()
        congrats_submission.mod.sticky()
    except Exception as e:
        send_reddit_message_to_self('Error encountered',
                                    message=('Could not sticky this post: {}    \n{}    \n\n'
                                             .format(congrats_shortlink, str(e))))
        pass

    # # Turn contest mode OFF on the original voting post
    # Need to do this in order to count the votes, otherwise all posts show 1 vote.
    voting_post.mod.contest_mode(state=False)

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
        generic_post = GenericPost(filename=winning_image, title=(post_title + ' ' + congrats_shortlink))
        social_media_dict = generic_post.post_to_all_social()
        send_reddit_message_to_self(title='The new Congratulations post has just posted.',
                                    message='The congrats post is here:    {}\n    \n{}    \n{}')\
            .format(str(congrats_shortlink), str(voting_post.shortlink), str(social_media_dict['tweet_url']))
    except Exception as e:
        send_reddit_message_to_self('Could not post to social media',
                                    message='Could not post announcement to socialmeda:    \n{}    \n\n').format(str(e))

    source = 'submissions_current.csv'
    destination = ('SubmissionsArchive/' + contest_year + '-' + contest_month + '-AllSubmissions.csv')
    shutil.move(source, destination)

    # # Send message to winner congratulating them
    congrats_message = ('[Congratulations, you won this month\'s Map Contest!](' + congrats_shortlink + ')    \n' +
                        bot_disclaimer_text)
    try:
        r.redditor(winner).message('Congratulations', congrats_message)
    except Exception as e:
        send_reddit_message_to_self(title='Could not send message to winner',
                                    message='Error: {}'.format(str(e)))
    log_db.add_row_to_db(diagnostics=my_diag.make_dict(), passfail=1)


if __name__ == "__main__":
    main()
