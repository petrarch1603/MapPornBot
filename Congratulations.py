from functions import *

# Verify before running in case of accidental execution.
# If this script is automated, this line will need to be deleted.
input('Are you ready?')

# # 1) Get the raw ID of the voting post.
# When the voting post is created the id is written to data/votingpostdata.txt
# That id is brought here to interact with that post.
votingpostdata = open('data/votingpostdata.txt', 'r')
raw_id = (votingpostdata.read())
submission = r.submission(id=raw_id)

# # 2) Prepare a new CSV with the top four maps.
# This will be referenced at the end of the year for the
# Annual map contest of best map of the year.
# # Get some month and year data for the previous month
date_10_days_ago = datetime.now() - timedelta(days=10)
contest_month = str(date_10_days_ago.strftime("%m"))
contest_month_pretty = str(date_10_days_ago.strftime("%B"))
contest_year = str(date_10_days_ago.date().year)
new_csv = str(contest_year + contest_month + 'TOP.csv')
submitFile = open('SubmissionsArchive/' + new_csv, 'w+').close()

# # 3) Prepare the loop for parsing contestant maps
# Prepare the text of the post.
# Congratulations_text is a boilerplate template for each month's congratulations post.
# There are a number of variables that need to be changed on this template though.
# We will do that in the for loop.
congratulations_text = open('Congratulations_text.txt', 'r')
data = congratulations_text.read()

# Sort top comments from the voting post
submission.comment_sort = 'top'
submission.comments.replace_more(limit=0) # This gets the top level comments in the submission

# Prepare a regex script to find the unique ID on each comment.
id_regex = re.compile(r'\^\^\^\^\w\w\w\w\w\w')
n = 0

# # 4) The Loop
# Gets top four highest upvoted comments and iterates thru them doing operations each time.
for comment in submission.comments[:4]:
    n = n+1
    mylist = [] # For each comment, we will create a list. Start with a blank list each time.
    mo = id_regex.search(comment.body) # Find those ID's
    message_id = str(mo.group()).replace('^^^^', '')
    # Open the CSV of submissions and index each field
    with open('submissions_current.csv') as current_csv:
        csvreader = csv.reader(current_csv)
        for row in csvreader:
            if message_id == row[4]:
                placemap = row[0]  # Get name of the map
                placeurl = row[1]  # Get URL of the map
                placedesc = row[2]  # Get description of the map
                placeuser = row[3]  # Get author of the map
    dummy = placedesc  # Pycharm is giving me a local variable error if I don't assign a variable to placedesc
    data = str(data)  # Data is the Congratulations text template, now we're going to replace variables
    data = data.replace(str('%' + str(n) + 'PLACEUSER%'), str(placeuser))
    data = data.replace(str('%' + str(n) + 'PLACEVOTES%'), str(comment.score))
    data = data.replace(str('%' + str(n) + 'PLACEMAP%'), str(placemap))
    data = data.replace(str('%' + str(n) + 'PLACEURL%'), str(placeurl))
    mylist.append(str(placemap))  # These lines create a list for the top posts of the month csv
    mylist.append(str(placeurl))
    mylist.append(str(placedesc))
    mylist.append(str(placeuser))
    mylist.append(message_id)
    with open('SubmissionsArchive/' + new_csv, 'a') as submitFile:
        reader = csv.reader(submitFile)
        wr = csv.writer(submitFile)  # Write the list in a comma delimited format
        wr.writerow(mylist)

# # 5) Post congratulations post to reddit

# Get the winner in a variable 'winner'
# Seems the easiest way to do this is to just get it from the first line of the CSV that we just created.
with open('SubmissionsArchive/' + new_csv, 'r') as submitFile:
    reader = csv.reader(submitFile)
    reader = list(reader)
    winner = reader[0][3]
    win_map_url = reader[0][1]

# Put the contest post URL into the congratulations template.
data = data.replace('%VOTINGPOSTURL%', submission.shortlink)
data = data.replace('%MYUSERID%', my_reddit_ID)
post_title = ('Congratulations to /u/' + winner + ': winner of ' + contest_month_pretty + '\'s Monthly Map Contest!')
submission = r.subreddit('mapporn').submit(post_title, selftext=data)  # Submits the post to Reddit
submission.mod.distinguish()
submission.mod.sticky()
congrats_shortlink = submission.shortlink

# # 6) Turn contest mode OFF on the original voting post
submission = r.submission(id=raw_id)
submission.mod.contest_mode(state=False)

# # 7) Post congratulations post to social media
# Download the image locally
filename = 'temp.jpg'
request = requests.get(win_map_url, stream=True)
if request.status_code == 200:
    with open(filename, 'wb') as image:
        for chunk in request:
            image.write(chunk)
    filesize = os.path.getsize('temp.jpg')
    if filesize > 3070000:  # If it's too big social media sites won't like it.
        os.remove(filename)
        filename='misc_images/01.png' # This is a backup image to post in lieu of the winning map.
else:
    filename='misc_images/01.png'

# Post to social media.
# Now that we have the image we can run the function to post it to the social media sites
thing = generic_post(imagefile='filename', message=(post_title + ' ' + congrats_shortlink))


# # 8) Send message to me with shortlinks for QC and social media URLs
message_to_me = ('The new Congratulations post has just posted.    \nThe congrats post is here: ' + congrats_shortlink + '   \n' + 'Verify that the original post has contest mode turned OFF: ' +
                 submission.shortlink + '   \n' + thing + '\nCheck the new CSV in the archives folder and make sure there is a description for each map. Pycharm was giving me trouble in assigning local variables during the FOR loop')
r.redditor(my_reddit_ID).message('Congratulation post posted', message_to_me)

# # 9) Rename and move the submissions_current.csv to a new name in the archive directory
source = 'submissions_current.csv'
destination = ('SubmissionsArchive/' +contest_year + '-' + contest_month + '-Submissions.csv')
shutil.move(source, destination)
