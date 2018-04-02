from functions import *

# Verify before running in case of accidental execution.
# If this script is automated, this line will need to be deleted.
input('Are you ready?')

# # 1) Get the raw ID of the voting post.
# When the voting post is created the id is written to congratsData/votingpostdata.txt
# That id is brought here to interact with that post.
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
contest_month = str(date_10_days_ago.strftime("%m"))
contest_month_pretty = str(date_10_days_ago.strftime("%B"))
contest_year = str(date_10_days_ago.date().year)
winners_csv = str(contest_year + contest_month + 'WINNERS.csv')

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
    with open('submissions_current.csv') as current_csv:  # Add reply in voting post with name of map creator
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
    with open('submissions_current.csv') as current_csv:
        csvreader = csv.reader(current_csv)
        for row in csvreader:
            if sortedItem[1] == row[4]:
                placemap = str(row[0])  # Get name of the map
                placeurl = str(row[1])  # Get URL of the map
                placedesc = str(row[2])  # Get description of the map
                placeuser = str(row[3])  # Get user (creator) of the map
    winnerList.extend((
        placemap,
        placeurl,
        placedesc,
        placeuser,
        str(sortedItem[1]),
        str(sortedItem[0])
    ))
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
post_title = ('Congratulations to /u/' + winner + ': winner of ' + contest_month_pretty + '\'s Monthly Map Contest!')
congratsSubmission = r.subreddit('mapporn').submit(post_title, selftext=congratsData)  # Submits the post to Reddit
congratulations_text.close()
congrats_shortlink = congratsSubmission.shortlink
congratsSubmission.mod.distinguish()
try:
    congratsSubmission.mod.approve()
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
                 votingPost.shortlink + '   \n' + str(generic_message) + '\nCheck the new CSV in the SubmissionsArchives folder and make sure there is a description for each map. Pycharm was giving me trouble in assigning local variables during the FOR loop')
send_reddit_message_to_self(title='Congratulation post posted', message=message_to_me)

# # 9) Rename and move the submissions_current.csv to a new name in the archive directory
source = 'submissions_current.csv'
destination = ('SubmissionsArchive/' + contest_year + '-' + contest_month + '-AllSubmissions.csv')
shutil.move(source, destination)

# # 10) Send message to winner congratulating them
congratsMessage = ('[Congratulations, you won this month\'s Map Contest!](' + congrats_shortlink + ')    \n' + bot_disclaimer_text)
r.redditor(winner).message('Congratulations', congratsMessage)