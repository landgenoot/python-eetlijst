from datetime import datetime, date

import unittest

import os
import time
import requests
import eetlijst

class MockResponse(object):
    """
    Very simple mock version of a response generated by the `requests' module.
    """

    def __init__(self, content, status_code=200, url=None):
        self.content = content
        self.status_code = status_code
        self.url = url

    @staticmethod
    def from_file(filename, status_code=200, url=None):
        filename = os.path.join(os.path.dirname(__file__), "data", filename)

        with open(filename, "r") as fp:
            content = fp.read()

        return MockResponse(content, status_code, url)

class EetlijstTest(unittest.TestCase):
    """
    Test cases for `eetlijst.py'. The module `requests' is monkey patched to
    mimic results of actual requests. In addition, the number of requests is
    logged to track all cach hits or misses.

    GET requests should be put in `self.test_get_response' and POST requests in
    `self.test_post_response'. Since responses are popped, they should be in
    reverse order.

    The test cases only test scraping and session management. Actual HTTP
    requests are not tested.
    """

    def setUp(self):
        requests.get = self.patched_get
        requests.post = self.patched_post

        self.counter = 0

    def patched_get(self, url, *args, **kwargs):
        self.counter += 1
        return self.test_get_response.pop()

    def patched_post(self, url, *args, **kwargs):
        self.counter += 1
        return self.test_post_response.pop()

    def test_login(self):
        """
        Test succesful login.
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b")
        ]

        try:
            client = eetlijst.Eetlijst(username="test", password="test", login=True)
        except eetlijst.LoginError:
            self.fail("LoginError raised")

    def test_login_failed(self):
        """
        Test unsuccesful login.
        """

        self.test_get_response = [
            MockResponse.from_file("test_login_failed.html", url="http://www.eetlijst.nl/login.php?r=failed")
        ]

        with self.assertRaises(eetlijst.LoginError):
            client = eetlijst.Eetlijst(username="test", password="invalid", login=True)

    def test_timeout_session(self):
        """
        Test session timeout and renewal.
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b"),
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=99ee78cf04dbea386a90b57743411b3d")
        ]

        eetlijst.TIMEOUT_SESSION = 2
        client = eetlijst.Eetlijst(username="test", password="test", login=True)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "99ee78cf04dbea386a90b57743411b3d")
        self.assertEqual(self.counter, 1)

        time.sleep(3)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "bc731753a2d0fecccf12518759108b5b")
        self.assertEqual(self.counter, 2)

        time.sleep(1)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "bc731753a2d0fecccf12518759108b5b")
        self.assertEqual(self.counter, 2)

    def test_timeout_session_extend(self):
        """
        Test if sessions are extended when used properly.
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b"),
        ]

        eetlijst.TIMEOUT_SESSION = 2
        client = eetlijst.Eetlijst(username="test", password="test", login=True)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "bc731753a2d0fecccf12518759108b5b")
        self.assertEqual(self.counter, 1)

        time.sleep(1)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "bc731753a2d0fecccf12518759108b5b")
        self.assertEqual(self.counter, 1)

        time.sleep(1)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "bc731753a2d0fecccf12518759108b5b")
        self.assertEqual(self.counter, 1)

        time.sleep(1)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "bc731753a2d0fecccf12518759108b5b")
        self.assertEqual(self.counter, 1)

    def test_timeout_page(self):
        """
        Test page cache timeout.
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b"),
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=99ee78cf04dbea386a90b57743411b3d")
        ]

        eetlijst.TIMEOUT_SESSION = 10
        eetlijst.TIMEOUT_CACHE = 2
        client = eetlijst.Eetlijst(username="test", password="test", login=True)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "99ee78cf04dbea386a90b57743411b3d")
        self.assertEqual(self.counter, 1)

        time.sleep(3)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "99ee78cf04dbea386a90b57743411b3d")
        self.assertEqual(self.counter, 2)

        time.sleep(1)

        client.get_noticeboard()
        self.assertEqual(client.get_session_id(), "99ee78cf04dbea386a90b57743411b3d")
        self.assertEqual(self.counter, 2)

    def test_name(self):
        """
        Test list name retrieval.
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b")
        ]

        client = eetlijst.Eetlijst(username="test", password="test")

        self.assertEqual(client.get_name(), u"Python-eetlijst")
        self.assertEqual(self.counter, 1)

    def test_noticeboard(self):
        """
        Test noticeboard retrieval.
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b")
        ]

        client = eetlijst.Eetlijst(username="test", password="test")

        self.assertEqual(client.get_noticeboard(), u"This is a test message!")
        self.assertEqual(self.counter, 1)

    def test_noticeboard_html(self):
        """
        Test noticeboard retrieval with HTML in it.
        """

        self.test_get_response = [
            MockResponse.from_file("test_main2.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b")
        ]

        client = eetlijst.Eetlijst(username="test", password="test")

        self.assertEqual(client.get_noticeboard(), u"This is a test message!\n\n\nwww.github.com/basilfx")
        self.assertEqual(self.counter, 1)


    def test_residents(self):
        """
        Test residents retrieval
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b")
        ]

        client = eetlijst.Eetlijst(username="test", password="test")
        residents = client.get_residents()

        self.assertListEqual(residents, [u"Unknown1", u"Unknown2", u"Unknown3", u"Unknown4", u"Unknown5"])
        self.assertEqual(self.counter, 1)

    def test_statuses(self):
        """
        Test residents diner statuses
        """

        self.test_get_response = [
            MockResponse.from_file("test_main.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b")
        ]

        client = eetlijst.Eetlijst(username="test", password="test")
        rows = client.get_statuses(limit=2)

        self.assertListEqual([ status.value for status in rows[0].statuses], [-1, -1, -1, -1, -1])
        self.assertListEqual([ status.value for status in rows[1].statuses], [1, -3, 0, 0, 0])

        self.assertEqual(rows[0].date, date(year=2014, month=3, day=29))
        self.assertEqual(rows[0].deadline, None)
        self.assertEqual(rows[0].has_deadline_passed(), False)

        self.assertEqual(rows[0].has_cook(), False)
        self.assertEqual(rows[1].has_cook(), True)
        self.assertEqual(rows[0].has_diners(), True)
        self.assertEqual(rows[1].has_diners(), True)
        self.assertListEqual(rows[0].get_cooks(), [])
        self.assertListEqual(rows[1].get_cooks(), [0])
        self.assertListEqual(rows[0].get_nones(), [])
        self.assertListEqual(rows[1].get_nones(), [2, 3, 4])
        self.assertListEqual(rows[0].get_diners(), [0, 1, 2, 3, 4])
        self.assertListEqual(rows[1].get_diners(), [1])
        self.assertListEqual(rows[0].get_diners_and_cooks(), [0, 1, 2, 3, 4])
        self.assertListEqual(rows[1].get_diners_and_cooks(), [0, 1])
        self.assertEqual(rows[0].get_count(), 5)
        self.assertEqual(rows[1].get_count(), 4)
        self.assertEqual(rows[0].get_count(rows[0].get_cooks()), 0)
        self.assertEqual(rows[1].get_count(rows[1].get_cooks()), 1)
        self.assertEqual(rows[0].get_count(rows[0].get_diners()), 5)
        self.assertEqual(rows[1].get_count(rows[1].get_diners()), 3)

        self.assertEqual(self.counter, 1)

    def test_statuses_deadline(self):
        """
        Test residents diner statuses with a deadline
        """

        self.test_get_response = [
            MockResponse.from_file("test_main3.html", url="http://www.eetlijst.nl/main.php?session_id=bc731753a2d0fecccf12518759108b5b")
        ]

        client = eetlijst.Eetlijst(username="test", password="test")
        rows = client.get_statuses(limit=1)

        self.assertEqual(rows[0].date, date(year=2014, month=3, day=30))
        self.assertEqual(rows[0].deadline, datetime(year=2014, month=3, day=30, hour=0, minute=0, second=0))
        self.assertEqual(rows[0].is_deadline_passed(), True)

        self.assertEqual(self.counter, 1)