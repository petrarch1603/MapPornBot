from functions import *

# Post the top /r/MapPorn submission from the last month.

loglist = []
loglist.append(datetime.datetime.now())

top = r.subreddit('mapporn').top('month', limit=1)
top = list(top)
top_month = (top[0])
announce_month = 'Top post of the month:\n'

try:
    output = shotgun_blast(raw_id_input=top_month, announce_input=announce_month)
    loglist.append(output)
except:
    loglist.append('Unable to post top post of the month')

with open('logs/prettylog.txt', 'a') as logfile:
    for i in loglist:
        logfile.write(str(i))
    logfile.write('-------------')
