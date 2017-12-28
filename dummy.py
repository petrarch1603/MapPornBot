from functions.py import *


# # 1) Get the raw ID of the voting post.
# When the voting post is created the id is written to congratsData/votingpostdata.txt
# That id is brought here to interact with that post.
votingpostdata = open('data/votingpostdata.txt', 'r')
raw_id = (votingpostdata.read())
votingPost = r.submission(id=raw_id)
bot_disclaimer_text = bot_disclaimer()

# # 2) Prepare a new CSV with the top four maps.
# This will be referenced at the end of the year for the
# Annual map contest of best map of the year.
# # Get some month and year congratsData for the previous month
date_10_days_ago = datetime.now() - timedelta(days=10)
contest_year = str(date_10_days_ago.date().year)
# winners_csv = str('BestOf' + contest_year + '.csv')

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




# Put the contest post URL into the congratulations template.
congratsData = congratsData.replace('%VOTINGPOSTURL%', votingPost.shortlink)
congratsData = congratsData.replace('%MYUSERID%', my_reddit_ID)
post_title = ('Congratulations to /u/' + 'winner' + ': winner of the best map of ' + contest_year + '!')
# congratsSubmission = r.subreddit('mapporn').submit(post_title, selftext=congratsData)  # Submits the post to Reddit
#congratulations_text.close()
#congrats_shortlink = congratsSubmission.shortlink
#congratsSubmission.mod.distinguish()

print(congratsData)