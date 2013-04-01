from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import copy
import datetime
import unittest
import mock

import pkg_resources

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

    def test_grab_json_with_json_auth(self):
        # This hits a real URL, but doesn't incur a rate limit.
        # The auth is a user/pass list (from json) but the requests lib needs
        # a tuple. This test checks whether it works properly that way.
        url = 'https://api.github.com/rate_limit'
        new_settings = copy.deepcopy(commits.SETTINGS)
        new_settings['auth'] = ['atilla_the_hun', 'nonexisting_password']
        with mock.patch('githubinfo.commits.SETTINGS', new_settings):
            result = commits.grab_json(url)
            self.assertEquals({'message': 'Bad credentials'}, result)

    def test_grab_paginated_json(self):
        # This hits a real URL and incurs a rate limit...
        # lizardsystem has more than 30 repos, which is the pagination limit.
        url = commits.ORG_REPOS_URL.format(organization='lizardsystem')
        result = commits.grab_json(url)
        print(result)
        self.assertTrue(len(result) > 30)

    def test_is_testfile1(self):
        self.assertTrue(commits.is_testfile(
                {'filename': 'myproject/tests.py'}))

    def test_is_testfile2(self):
        self.assertTrue(commits.is_testfile(
                {'filename': 'myproject/test_thingy.js'}))

    def test_is_testfile3(self):
        self.assertFalse(commits.is_testfile(
                {'filename': 'myproject/testsettings.py'}))

    def test_is_testfile4(self):
        self.assertFalse(commits.is_testfile(
                {'filename': 'myproject/README.rst',
                 'patch': ''}))

    def test_is_testfile5(self):
        # Detect relevant changes in doctests.
        self.assertTrue(commits.is_testfile(
                {'filename': 'myproject/something.rst',
                 'patch': '@@ -1,6 +1,12 @@\n >>> print("reinout")'}))

    @mock.patch('githubinfo.commits.SETTINGS', {})
    def test_load_custom_settings(self):
        testsettings = pkg_resources.resource_filename('githubinfo.commits',
                                                       'testsettings.json')
        commits.load_custom_settings(testsettings)
        self.assertTrue('auth' in commits.SETTINGS)


def mock_commit_grabber1(url):
    return {'files': [{'filename': 'myproject/README.txt',
                       'patch': ''}]}


def mock_commit_grabber2(url):
    return {'files': [{'filename': 'myproject/README.txt',
                       'patch': ''},
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


class TestCommitCounterTest(unittest.TestCase):

    def setUp(self):
        self.a = commits.TestCommitCounter()
        self.b = commits.TestCommitCounter()

    def test_smoke(self):
        self.assertTrue(self.a)

    def test_sorting(self):
        # More testcommits? On top.
        self.a.num_testcommits = 10
        self.b.num_testcommits = 5
        some_list = [self.b, self.a]
        some_list.sort()
        self.assertEquals(some_list[0], self.a)

    def test_sorting2(self):
        # Equal qua testcommits? Percentage wins.
        self.a.num_testcommits = 10
        self.b.num_testcommits = 10
        self.a.num_commits = 10
        self.b.num_commits = 20
        some_list = [self.b, self.a]
        some_list.sort()
        self.assertEquals(some_list[0], self.a)

    def test_add_commit1(self):
        commit = mock.Mock()
        commit.is_testcommit = False
        commit.num_testfiles_changed = 0
        self.a.add_commit(commit)
        self.assertEquals(self.a.num_commits, 1)
        self.assertEquals(self.a.num_testcommits, 0)

    def test_add_commit2(self):
        commit = mock.Mock()
        commit.is_testcommit = True
        commit.num_testfiles_changed = 3
        self.a.add_commit(commit)
        self.a.add_commit(commit)  # Another time!
        self.assertEquals(self.a.num_commits, 2)
        self.assertEquals(self.a.num_testcommits, 2)
        self.assertEquals(self.a.testfiles_changed, 6)

    def test_no_percentage(self):
        # No tests? No percentage. Those "(0%)" strings are boring.
        # Printing out a ready-to-fill-in hitman contract would perhaps be
        # better, but let's not get carried away right now with our Test
        # Coverage Improvement Campaign, shall we?
        self.a.num_commits = 20
        self.assertEquals(self.a.percentage, '')

    def test_percentage(self):
        self.a.num_commits = 20
        self.a.num_testcommits = 10
        self.assertEquals(self.a.percentage, '(50%)')

    def test_print_info(self):
        self.a.name = 'Some name'
        with mock.patch('sys.stdout') as mock_stdout:
            self.a.print_info()
            self.assertTrue(mock_stdout.write.called)


class MockCommit(mock.Mock):
    user = 'reinout'
    is_testcommit = True
    num_testfiles_changed = 1


class ProjectTest(unittest.TestCase):

    def setUp(self):
        self.project = commits.Project('nens', 'githubinfo', {})

    @mock.patch('githubinfo.commits.Project.load_branches')
    @mock.patch('githubinfo.commits.Project.load_project_commits')
    @mock.patch('githubinfo.commits.Project.load_individual_commits')
    def test_load(self, patched_1, patched_2, patched_3):
        # Calling load() loads the various json files.
        self.project.load()
        self.assertTrue(patched_1.called)
        self.assertTrue(patched_2.called)
        self.assertTrue(patched_3.called)

    def test_is_active1(self):
        self.assertFalse(self.project.is_active)

    def test_is_active2(self):
        self.project.num_commits = 428391
        self.assertTrue(self.project.is_active)

    @mock.patch('githubinfo.commits.grab_json', lambda url: [])
    def test_load_branches(self):
        self.assertEquals(self.project.load_branches(), [])

    @mock.patch('githubinfo.commits.grab_json', lambda url: [
            {'commit': {'sha': 'asdfghjkl'}},])
    def test_load_branches2(self):
        self.assertEquals(self.project.load_branches(), ['asdfghjkl'])

    def test_load_project_commits(self):
        self.project.branch_SHAs = []
        self.assertEquals(self.project.load_project_commits(), [])

    @mock.patch('githubinfo.commits.grab_json', lambda url, params: ['a'])
    def test_load_project_commits2(self):
        self.project.branch_SHAs = ['fsdfwrwesdfsdfsdf',
                                    'dfsdrrterdxcxcvcx']
        self.assertEquals(self.project.load_project_commits(), ['a', 'a'])

    @mock.patch('githubinfo.commits.Commit', MockCommit)
    def test_load_individual_commits(self):
        self.project.commits = [{'some': 'dict'}]
        self.project.users['reinout'] = commits.User()
        self.project.load_individual_commits()
        self.assertEquals(self.project.users['reinout'].num_commits, 1)
        self.assertEquals(self.project.num_commits, 1)

    @mock.patch('githubinfo.commits.Commit', MockCommit)
    def test_load_individual_commits_with_restriction1(self):
        # Add a commit that is a known user.
        self.project.restrict_to_known_users = True
        self.project.commits = [{'some': 'dict'}]
        self.project.users['reinout'] = commits.User()
        self.project.load_individual_commits()
        self.assertEquals(self.project.users['reinout'].num_commits, 1)
        self.assertEquals(self.project.num_commits, 1)

    @mock.patch('githubinfo.commits.Commit', MockCommit)
    def test_load_individual_commits_with_restriction2(self):
        # Add a commit that is not a known user: it isn't added.
        self.project.restrict_to_known_users = True
        self.project.commits = [{'some': 'dict'}]
        self.project.load_individual_commits()
        self.assertEquals(self.project.num_commits, 0)
