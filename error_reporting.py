import pymongo
from secrets import *
from functions import *
import time

past_week = (time.time() - 605000)
connection = pymongo.MongoClient("mongodb://" + mongo_id + ":" + mongo_pw + mongo_db)
db = connection.mappornstatus
collection = db.mappornstatus

# Finds all errors from the past week
cursor = db.mappornstatus.find({'time': {"$gt": past_week}, "error": {"$exists": "true"}})
errorslist = []
for document in cursor:
    script = document["object"]['script']
    error = document["error"]
    time = time.strftime('%A %H:%M', time.localtime(document["time"]))
    error_msg = ("The " + script + " script failed. The error message states: "
                 + error + ". The script ran " + str(time) + ".\n")
    errorslist.append(error_msg)

message = ("\n".join(errorslist))
send_reddit_message_to_self("Weekly Error Reporting", message)