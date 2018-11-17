"""Script for testing the checkinbox.py script"""
import os
import sys
import unittest
from unittest import mock, TestCase
sys.path.append('../')
from checkinbox import contest_message as c_m, \
                       socmedia_message as s_m, \
                       dayinhistory_message as h_m, \
                       other_message as o_m

os.chdir('..')


# All functions in checkinbox that add to database will use this call
expected_call = "call().add_row_to_db(script='checkinbox.py')"


class TestCheckInbox(TestCase):
    """Tests for checking inbox"""

    @mock.patch('classes.MapRow', autospec=True)
    @mock.patch('classes.ContestDB')
    @mock.patch('functions.send_reddit_message_to_self', autospec=True)
    def test_contest_submission(self, mock_reddit_message, mock_contest_db, mock_maprow):
        for obj in mock_cont_msgs:

            c_m(message=obj)

            # Make sure the function creates a maprow object
            mock_maprow.assert_called_with(schema=mock_contest_db().schema,
                                           table=mock_contest_db().table,
                                           row=obj.expected)

            # Make sure the function adds row to database
            assert str(mock_maprow.mock_calls[1]) == expected_call

            # Make sure the function sends a New Map Submitted message to me on Reddit
            args, kwargs = mock_reddit_message.call_args
            assert kwargs['title'] == 'New Map Submitted!'

            # Make sure the function replies to user
            obj.reply.assert_called_once()

            # Make sure the function marks message read
            obj.mark_read.assert_called_once()

    @mock.patch('praw.Reddit.submission', autospec=True)
    @mock.patch('classes.MapRow', autospec=True)
    @mock.patch('functions.send_reddit_message_to_self', autospec=True)
    def test_socmedia_message(self, mock_reddit_message, mock_maprow, mock_praw):
        for obj in mock_soc_msgs:

            # Make a fake praw reddit title
            mock_praw(self, id='obj.id').title = obj.title

            s_m(message=obj)

            if mock_maprow.called:
                mock_maprow.assert_called_with(path=mock.ANY,
                                               schema=mock.ANY,
                                               table=mock.ANY,
                                               row=obj.expected_row)
                assert str(mock_maprow.mock_calls[1]) == expected_call
                obj.mark_read.assert_called_once()
                mock_maprow.reset_mock()
            if mock_reddit_message.called:
                args, kwargs = mock_reddit_message.call_args
                expected_title = str(obj.expected_reddit_message)
                assert kwargs['title'] == expected_title

                if kwargs['title'] != "No time zones found":
                    mock_maprow.assert_not_called()
                obj.mark_read.assert_called_once()
                mock_reddit_message.reset_mock()
            mock_praw.reset_mock()

    @mock.patch('classes.MapRow', autospec=True)
    @mock.patch('functions.send_reddit_message_to_self', autospec=True)
    def test_history_message(self, mock_reddit_message, mock_maprow):
        for obj in mock_hist_msgs:

            h_m(obj)

            if mock_maprow.called:
                mock_maprow.assert_called_with(path=mock.ANY,
                                               schema=mock.ANY,
                                               table=mock.ANY,
                                               row=obj.expected_row)
                assert str(mock_maprow.mock_calls[1]) == expected_call
                obj.mark_read.assert_called_once()
                mock_maprow.reset_mock()
            if mock_reddit_message.called:
                args, kwargs = mock_reddit_message.call_args
                expected_title = str(obj.expected_reddit_message)
                assert kwargs['title'] == expected_title

                # If there is a reddit message to self it is because of an error and the database should not be touched
                mock_maprow.assert_not_called()
                obj.mark_read.assert_called_once()
                mock_reddit_message.reset_mock()

    @mock.patch('functions.send_reddit_message_to_self', autospec=True)
    def test_other_message(self, mock_reddit_message):
        for obj in mock_oth_msgs:
            o_m(obj)
            args, kwargs = mock_reddit_message.call_args
            expected_title = str(obj.expected_reddit_message)
            assert kwargs['title'] == expected_title
            obj.mark_read.assert_called_once()
            mock_reddit_message.reset_mock()


if __name__ == '__main__':
    unittest.main()


"""These are the mock messages that are tested."""
mock_cont_msg1 = mock.Mock()
mock_cont_msg1.body = "Map Name: TESTYour Map's Name\n\nLink: https://TEST.it/829bsssx6xv11.jpg\n\n" \
               "TESTDescription: San Francisco Cable Car System, 1892"
mock_cont_msg1.id = 'TESTeq'
mock_cont_msg1.author = 'TESTAUTHOR'
mock_cont_msg1.subject = "Map Contest Submission"
mock_cont_msg1.expected = ["TESTYour Map's Name",
                           "https://TEST.it/829bsssx6xv11.jpg",
                           "TESTDescription: San Francisco Cable Car System, 1892",
                           mock_cont_msg1.author,
                           mock_cont_msg1.id]
mock_cont_msgs = [mock_cont_msg1]

mock_soc_msg1 = mock.Mock()
mock_soc_msg1.body = "https://redd.it/TEST11\nTEST TITLE\n0"
mock_soc_msg1.expected_row = ['TEST11', 'TEST TITLE', 99, 0, mock.ANY, 0]
mock_soc_msg1.author = 'Petrarch1603'
mock_soc_msg1.subject = 'socmedia'
mock_soc_msg1.expected_reddit_message = "No time zones found"

mock_soc_msg2 = mock.Mock()
mock_soc_msg2.body = "https://www.google.com\n"
mock_soc_msg2.author = 'Petrarch1603'
mock_soc_msg2.subject = 'socmedia'
mock_soc_msg2.expected_reddit_message = "Socmedia Message Error"

mock_soc_msg3 = mock.Mock()
mock_soc_msg3.body = "https://redd.it/TEST12\n"
mock_soc_msg3.id = "TEST12"
mock_soc_msg3.title = "London"
mock_soc_msg3.author = 'Petrarch1603'
mock_soc_msg3.subject = 'socmedia'
mock_soc_msg3.expected_row = ['TEST12', mock_soc_msg3.title, 0, 1, mock.ANY, 0]
mock_soc_msg3.expected_reddit_message = ""

mock_soc_msgs = [mock_soc_msg1, mock_soc_msg2, mock_soc_msg3]

mock_hist_msg1 = mock.Mock()
mock_hist_msg1.body = "https://redd.it/TEST31\nTEST TITLE\n100"
mock_hist_msg1.expected_row = ['TEST31', "TEST TITLE", 100]

mock_hist_msg2 = mock.Mock()
mock_hist_msg2.body = "https://redd.it/TEST31\n100"
mock_hist_msg2.expected_reddit_message = "Error processing day in history"

mock_hist_msg3 = mock.Mock()
mock_hist_msg3.body = "https://redd.it/TEST31\nTEST TITLE\n400"
mock_hist_msg3.expected_reddit_message = "Error processing day in history"

mock_hist_msgs = [mock_hist_msg1, mock_hist_msg2, mock_hist_msg3]

mock_oth_msg1 = mock.Mock()
mock_oth_msg1.body = "Hey here's a suggestion"
mock_oth_msg1.author = "USERNPC"
mock_oth_msg1.subject = "Suggestion"
mock_oth_msg1.expected_reddit_message = "Message sent to Bot, Please check on it"

mock_oth_msgs = [mock_oth_msg1]
