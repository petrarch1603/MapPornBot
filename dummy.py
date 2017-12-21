from functions import *
import csv

submission = r.submission(id='7l5yax')
shortlink = submission.shortlink
botDisclaimerText = bot_disclaimer()

finalistsCSV = 'SubmissionsArchive/finalists2017.csv'

f = open(finalistsCSV, 'r')
reader = csv.reader(f)
title_to_finalist = 'The Annual Best Map of the Year contest is now live!'
message_to_finalist = ('**The Annual Best Map of the Year contest is now live!**    \nThank you for contributing a map. [The voting on the contest is open now at this link.]('
                               + shortlink + ')    \n' + botDisclaimerText)

for row in reader:
    try:
        print(row[3])
        r.redditor(row[3]).message(title_to_finalist, message_to_finalist)
    except:
        print('Error sending message to ' + row[3])
print(shortlink)
