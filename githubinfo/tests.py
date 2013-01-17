from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime
import unittest
import mock

from githubinfo import commits

FIXED_DATE = datetime.datetime(year=1972, month=12, day=25)


class UtilitiesTest(unittest.TestCase):

    def test_since(self):
        def mock_now():
            return FIXED_DATE
        with mock.patch('datetime.datetime') as dt:
            dt.now = mock_now
            self.assertEquals(commits.since(), '1972-12-18T00:00:00')

    def test_grab_json(self):
        # This hits a real URL, but doesn't incur a rate limit.
        url = 'https://api.github.com/rate_limit'
        result = commits.grab_json(url)
        print("In case the tests, fail, perhaps it is because of the github")
        print("rate limit. Some of the tests really hit the API...")
        print(result)
        self.assertTrue('rate' in result)

    def test_grab_paginated_json(self):
        # This hits a real URL and incurs a rate limit...
        # lizardsystem has more than 30 repos, which is the pagination limit.
        url = commits.ORG_REPOS_URL.format(organisation='lizardsystem')
        result = commits.grab_json(url)
        print(result)
        self.assertTrue(len(result) > 30)

    def is_testfile1(self):
        self.assertTrue(commits.is_testfile('myproject/tests.py'))

    def is_testfile2(self):
        self.assertTrue(commits.is_testfile('myproject/test_thingy.js'))

    def is_testfile3(self):
        self.assertFalse(commits.is_testfile('myproject/testsettings.py'))

    def is_testfile4(self):
        self.assertFalse(commits.is_testfile('myproject/README.rst'))


def mock_commit_grabber1(url):
    return {'files': [{'filename': 'myproject/README.txt'}]}


def mock_commit_grabber2(url):
    return {'files': [{'filename': 'myproject/README.txt'},
                      {'filename': 'myproject/tests.py'}]}


class CommitTest(unittest.TestCase):
    sample_commit_dict = {
        'commit': {
            'committer': {
                'name': 'Reinout van Rees'
                },
            },
        'url': 'http://example.org/dummy',
        }

    @mock.patch('githubinfo.commits.grab_json')
    def test_init(self, patched_grab_json):
        commit = commits.Commit(self.sample_commit_dict)
        self.assertEquals(commit.user, 'Reinout van Rees')

    @mock.patch('githubinfo.commits.grab_json', new=mock_commit_grabber1)
    def test_no_testcommits(self):
        commit = commits.Commit(self.sample_commit_dict)
        self.assertFalse(commit.is_testcommit)

    @mock.patch('githubinfo.commits.grab_json', new=mock_commit_grabber2)
    def test_testcommits(self):
        commit = commits.Commit(self.sample_commit_dict)
        self.assertTrue(commit.is_testcommit)
