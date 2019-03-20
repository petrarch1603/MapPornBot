"""Script for checking Reddit Bot's Inbox

Checks for following message:

    * Map Contest Submission
    * Social Media Map
        Adds this map to the SocMedia database. Every three hours a map from this database is posted to social media.
    * Day in History map
    * All other messages sent from users to the bot.

"""

import classes
import csv
import functions
import os
import praw
import requests
import time
from WhereWorld import get_image_name

r = praw.Reddit('bot1')
my_reddit_id = 'Petrarch1603'
script = str(os.path.basename(__file__))
disclaimer = functions.bot_disclaimer()
MessageReply = 'Your map has been received.   ' + '\n' + 'Look for the voting post for the contest soon.    ' + '\n' + \
               '&nbsp;       ' + '\n' + disclaimer


class WhereWorldRow:
    """
    Self-running class to parse Where World Messages.
    * Downloads the image locally
    * Adds row to CSV with url, and answer
    * Send Message to bot, subject: 'WW' with two lines:
    *                                                      url
    *                                                      answer_text
    """

    def __init__(self, msg_obj, csv_path='data/locations.csv'):
        self.csv_path = csv_path
        self.msg_obj = msg_obj
        self.next_date = ''
        self.answer_text = ''
        self.url = ''
        self.script_execution = True
        self.main()

    def _get_next_date(self):
        list_of_images = []
        for file in os.listdir('WW/'):
            if file[:4].isdigit():
                list_of_images.append(int(file[:4]))
        self.next_date = (max(list_of_images) + 1)
        this_week = int(get_image_name())
        if self.next_date <= (this_week + 1):
            self.next_date = this_week + 2
        print(self.next_date)

    def _parse_message(self):

        msg = functions.split_message(self.msg_obj.body)
        try:
            assert len(msg) == 2
        except AssertionError:
            functions.send_reddit_message_to_self(title="Error with Where World Inbox Check",
                                                  message='Length of message not two lines.')
            self.script_execution = False
            return False
        if msg[0].startswith("http"):
            self.url = msg[0]
            self.answer_text = msg[1]
        else:
            self.url = msg[1]
            self.answer_text = msg[0]

    def _add_ww_to_csv(self):
        my_csv_row = [self.next_date, self.answer_text, self.url]
        with open(self.csv_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(my_csv_row)
        print("Added row to csv")

    def _download_image(self):
        try:
            assert len(str(self.next_date)) == 4
        except AssertionError:
            functions.send_reddit_message_to_self(title="Error with Where World Check inbox",
                                                  message="Problem getting file name right, cannot"
                                                          "download image.")
            self.script_execution = False
            return False
        req = requests.get(self.url)
        my_file_name = 'WW/' + str(self.next_date) + '.png'
        print("New File Name: " + str(my_file_name))
        with open(my_file_name, 'wb') as f:
            f.write(req.content)
        fsize = os.stat(my_file_name).st_size
        if fsize >= 3200000:
            functions.send_reddit_message_to_self(title='ww error',
                                                  message='image too big!')
        print('Finished Downloading')

    def main(self):
        while self.script_execution is True:
            self._get_next_date()
            self._parse_message()
            self._add_ww_to_csv()
            self._download_image()
            print('Added WW map successfully')
            self.script_execution = False


def init(path: str = 'data/mapporn.db') -> None:
    """Initializes databases, Reddit bot

    :param path: database path
    :type path: str

    """
    global hist_db, log_db, r, soc_db
    hist_db = classes.HistoryDB(path=path)
    log_db = classes.LoggingDB(path=path)
    soc_db = classes.SocMediaDB(path=path)


def main() -> None:
    """Main script to check inbox"""

    for message in r.inbox.unread():
        init()

        # # Map Contest Submissions
        if message.subject == "Map Contest Submission":
            contest_message(message=message)
            message.mark_read()

        # # Social Media Maps
        elif message.subject == 'socmedia' and message.author == my_reddit_id:
            socmedia_message(message=message)
            message.mark_read()

        # # Day in History Messages
        elif message.subject == 'dayinhistory' and message.author == my_reddit_id:
            dayinhistory_message(message=message)
            message.mark_read()

        # # Where World Maps
        elif message.subject == 'WW' and message.author == my_reddit_id:
            WhereWorldRow(message)
            message.mark_read()

        # # Catch any other message a random user might have sent to the bot
        else:
            other_message(message=message)
            message.mark_read()


def contest_message(message, path: str = 'data/mapporn.db'):
    """Parse the praw message object and create a list for each map contest submission

    :param message: praw message object
    :type message: obj
    :param path: path to database (available for using a test database)

    """

    submission = functions.split_message(message.body)
    submission = [w.replace('Link:', '') for w in submission]  # Replace the title 'Link: ' with blankspace.
    submission = [w.replace('Map Name:', '') for w in submission]
    for i, v in enumerate(submission):
        submission[i] = submission[i].lstrip().rstrip()
    cont_db = classes.ContestDB(path=path)
    map_name = submission[0]
    url = submission[1]
    if url == 'http://imgur.com/replacethis.png':
        my_title = 'Problem with Map Contest Submission'
        my_message = 'There was a problem with your map contest submission for: ' + map_name + '   \n' + \
                  'The URL: ' + url + ' appears to be invalid.   \n' + \
                  '[Please resubmit your submission.](https://www.reddit.com/message/compose/?to=mappornbot&subject=' \
                  'Map%20Contest%20Submission&message=Map%20Name:%20Your%20Map%27s%20Name%0A%0ALink:%20' \
                  'http://imgur.com/replacethis.png%0A%0ADescription:%20Replace%20with%201-3%20Sentences.)'
        functions.send_reddit_message_to_user(title=my_title, message=my_message, user=str(message.author))
        message.mark_read()
        return
    if len(submission) > 3:
        submission[2] = str(submission[2]) + '\n' + str(submission[3])
    desc = submission[2]
    if desc.startswith("Description: "):
        desc = str(desc)[13:]
    author = message.author
    raw_id = str(message.id)
    my_list = [str(map_name), str(url), str(desc), str(author), str(raw_id)]

    my_table = "Time Zone|Map Count\n-|-\n"
    my_table += "Map Name:|{}\n".format(str(map_name))
    my_table += "URL:|{}\n".format(str(url))
    my_table += "Desc:|{}\n".format(str(desc))
    my_table += "Author:|{}\n".format(str(author))
    my_table += "Raw ID:|{}\n".format(str(raw_id))
    if path == 'data/mapporn.db':
        functions.send_reddit_message_to_self(title='New Map Submitted!',
                                              message=my_table)

    row_obj = classes.ContRow(schema=cont_db.schema, row=my_list, table=cont_db.table, path=path)
    row_obj.add_row_to_db(script=script)
    message.reply(MessageReply)
    message.mark_read()


def socmedia_message(message, path: str = 'data/mapporn.db'):
    """Parses social media message and adds it to SocMediaDB

    :param message: Praw message object
    :type message: obj
    :param path: path to database
    :type path: str

    """
    socmediamap = functions.split_message(message.body)
    for i, v in enumerate(socmediamap):
        socmediamap[i] = socmediamap[i].lstrip().rstrip()

    # Verify that there is a Reddit shortlink in the message
    try:
        assert socmediamap[0].startswith("https://redd.it/")
    except Exception as e:
        error_message = ("Error detected: Message does not include a valid URL   \n{}   \n\n".format(e) +
                         str(message.body))
        functions.send_reddit_message_to_self(title="Socmedia Message Error", message=error_message)
        message.mark_read()
        return

    # Get raw_id and set default values for fresh_status and date_posted
    raw_id = socmediamap[0][-6:]
    fresh_status = 1
    date_posted = 'NULL'
    post_error = 0
    table = 'socmediamaps'

    # Get title and clean it up - adjust fresh status if third line is 0
    if len(socmediamap) > 2 and str(socmediamap[2]) == '0':
        fresh_status = 0
        date_posted = int(time.time())
        title = socmediamap[1]
    elif len(socmediamap) > 1:
        title = socmediamap[1]
    else:
        r = praw.Reddit('bot1')  # Leave this line for testing (need to patch this call in unittests)
        title = r.submission(id=raw_id).title

    # Remove double quotes, very important for inserting into database
    title = classes.ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))

    # Get time_zone
    time_zone = functions.get_time_zone((functions.strip_punc(title)))
    if time_zone == 99 and path == 'data/mapporn.db':
        my_message = ("No time zone parsed from this title.    \n"
                      "Check it and see if there are any "
                      "locations to add to the CSV.    \n" + str(title) + "   \n" + str(soc_db.fresh_count))
        functions.send_reddit_message_to_self(title="No time zones found", message=my_message)

    # Put all the variables in the list to pass to MapRow
    my_maprow_list = [raw_id,
                      title,
                      time_zone,
                      fresh_status,
                      date_posted,
                      post_error]

    # Create MapRow Object and add to database
    my_maprow = classes.SocRow(schema=classes.schema_dict[table], row=my_maprow_list, table=table, path=path)
    try:
        my_maprow.add_row_to_db()
    except Exception as e:

        functions.send_reddit_message_to_self(title='error adding to database',
                                              message="Socmedia Script Problem: {}   "
                                                      "\n{}    \n{}".format(e,
                                                                            script,
                                                                            my_maprow_list))
    message.mark_read()


def dayinhistory_message(message, path: str = 'data/mapporn.db') -> None:
    """Parses dayinhistory message and adds it to HistoryDB

    :param message: Praw message object
    :type message: obj
    :param path: database path
    :type path: str

    """
    # Split message into a list
    dih_message = functions.split_message(message.body)
    day_of_year = ''
    raw_id = ''
    title = ''
    table = 'historymaps'
    # Parse Message
    for item in dih_message:

        try:
            item = int(item)
        except ValueError:
            pass
        if isinstance(item, int) and 0 < item < 366:
            day_of_year = item
        elif str(item).startswith("https://redd.it/"):
            raw_id = item.lstrip().rstrip()[-6:]
        else:
            title = item

    # Validate all parameters are included
    if title == '' or raw_id == '' or day_of_year == '':
        error_message = 'Error: Missing parameters \n'
        for line in dih_message:
            error_message += (line + '\n')
        functions.send_reddit_message_to_self(title='Error processing day in history',
                                              message=error_message)
        message.mark_read()
        return
    title = classes.ShotgunBlast.remove_text_inside_brackets(title.replace("\"", "'"))

    # Create MapRow and add to database
    my_maprow_list = [raw_id, title, day_of_year]
    my_maprow = classes.HistRow(schema=classes.schema_dict[table], row=my_maprow_list, table=table, path=path)
    try:
        my_maprow.add_row_to_db(script=script)
    except Exception as e:
        functions.send_reddit_message_to_self(title='error adding to database',
                                              message="history Script Problem: {}   \n{}".format(e, script))
    message.mark_read()


def other_message(message) -> None:
    """Receives all other messages sent to bot, and passes it on to a human for further processing

    :param message: praw message object
    :type message: obj

    """
    msg = message.body
    author = str(message.author)
    subject = message.subject
    functions.send_reddit_message_to_self(title='Message sent to Bot, Please check on it',
                                          message='*/u/{author}* sent this message to the bot. '
                                                  'Please check on it.    \n**Subject:**{subj}     \n**Message:**   \n'
                                                  '{msg}'.format(author=author,
                                                                 subj=subject,
                                                                 msg=msg))
    message.mark_read()


if __name__ == '__main__':
    functions.check_for_word_and_process()
    new_message = False
    init()
    for _ in r.inbox.unread():
        new_message = True
    if new_message is False:
        mydiag = classes.Diagnostic(script=str(os.path.basename(__file__)))
        mydiag.traceback = "No New Mail"
        log_db.add_row_to_db(diagnostics=mydiag.make_dict(), passfail=1)
        exit()
    main()
