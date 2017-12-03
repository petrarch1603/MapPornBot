from functions import *

for message in r.inbox.messages(limit=3):
    print(message.subject)
    print(message.body)
    print(message.author)
    print(message)
