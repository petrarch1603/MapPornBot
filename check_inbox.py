from functions import *

for message in r.inbox.messages(limit=1):
    print(message.subject)
    print(message.body)
    print(message.author)
    print(message)
