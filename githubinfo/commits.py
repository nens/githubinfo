from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from collections import defaultdict
from pprint import pprint
import datetime
import json
import os

import requests

ORG_REPOS_URL = 'https://api.github.com/orgs/{organization}/repos'
COMMITS_URL = 'https://api.github.com/repos/{owner}/{project}/commits'
BRANCHES_URL = 'https://api.github.com/repos/{owner}/{project}/branches'
VERBOSE = True  # Just for debugging.

# Settings are global and can be modified by some setup/init method.
SETTINGS = {
    'auth': None,  # Set it to ('username', 'very_secret').
    'days': 7,
    'organizations': [
        'ddsc',
        'lizardsystem',
        'nens',
        ],
    'extra_projects': [
        # ('organization', 'project'),
        ('reinout', 'buildout'),
        ('reinout', 'django-rest-framework'),
        ('reinout', 'serverinfo'),
        ('reinout', 'z3c.dependencychecker'),
        ('rvanlaar', 'djangorecipe'),
        ('zestsoftware', 'zest.releaser'),
        ],
    }


def debug(msg):
    """Print message if we want debug stuff."""
    if VERBOSE:
        print(msg)


def since():
    """Return iso-formatted string for github from-that-date query."""
    now = datetime.datetime.now()
    a_while_ago = now - datetime.timedelta(days=SETTINGS['days'])
    return a_while_ago.isoformat()


def grab_json(url, params=None, second_try=False):
    """Return json from URL, including handling pagination."""
    auth = SETTINGS['auth']
    if isinstance(auth, list):
        auth = tuple(auth)
    req = requests.get(url, auth=auth, params=params)
    if req.status_code == 401 and not second_try:
        # Unauthorized. Somehow this happens to me in rare cases.
        # Retry it once.
        print("Got a 401 unauthorized on %s, retrying it" % url)
        return grab_json(url, params=params, second_try=True)
    result = req.json()
    is_expected_type = (isinstance(result, list) or isinstance(result, dict))
    if not is_expected_type and not second_try:
        # Wrong type. String error message, probably.
        # Retry it once.
        print("Got a wrong type (%r) on %s, retrying it" % (result, url))
        return grab_json(url, params=params, second_try=True)
    if req.links.get('next'):
        # Paginated content, so we want to grab the rest.
        url = req.links['next']['url']
        # The assumption is "paginated content means it is a list".
        result += grab_json(url, params=params)
    return result


def is_testfile(fileinfo):
    filepath = fileinfo['filename']
    if 'testsettings.py' in filepath:
        # This one almost always doesn't have anything to do with
        # an added test.
        return False
    if 'test' in filepath:
        return True
    if filepath.endswith('.rst') or filepath.endswith('.txt'):
        # Possible doctest.
        if '>>>' in fileinfo.get('patch', ''):
            return True
    return False


def load_custom_settings(settings_file='settings.json'):
    """Update our default settings with the json found in the settings file.
    """
    # Note: settings_file is only a kwarg to make it testable.
    if os.path.exists(settings_file):
        custom_settings = json.loads(open(settings_file).read())
        SETTINGS.update(custom_settings)


class Commit(object):
    """Wrapper around a commit dict from github's API."""

    def __init__(self, the_dict):
        self.num_testfiles_changed = 0
        self.user = the_dict['commit']['committer']['name']
        commit_url = the_dict['url']
        commit_info = grab_json(commit_url)
        for changed_file in commit_info.get('files', []):
            if is_testfile(changed_file):
                self.num_testfiles_changed += 1
                debug("Test file: {}".format(changed_file['filename']))

    @property
    def is_testcommit(self):
        return bool(self.num_testfiles_changed)


class TestCommitCounter(object):

    def __init__(self):
        self.num_commits = 0
        self.num_testcommits = 0
        self.testfiles_changed = 0

    def __cmp__(self, other):
        return cmp((-self.num_testcommits, self.num_commits),
                   (-other.num_testcommits, other.num_commits))

    def add_commit(self, commit):
        self.num_commits += 1
        if commit.is_testcommit:
            self.num_testcommits += 1
            self.testfiles_changed += commit.num_testfiles_changed

    @property
    def percentage(self):
        """Return percentage of test commits to total.

        Return it as a string including parentheses.

        If there are no test commits, omit the percentage.
        """
        if not self.num_testcommits:
            return ''
        result = str(int(100.0 * self.num_testcommits / self.num_commits))
        return '({}%)'.format(result)

    def print_info(self):
        msg = "{name}: {tested} {percentage}"
        print(msg.format(name=self.name,
                         tested=self.num_testcommits,
                         percentage=self.percentage))


class Project(TestCommitCounter):

    def __init__(self, owner, project, users,
                 restrict_to_known_users=False):
        super(Project, self).__init__()
        self.owner = owner
        self.name = project
        self.users = users
        self.restrict_to_known_users = restrict_to_known_users

    def load(self):
        debug("Loading project {}...".format(self.name))
        self.branch_SHAs = self.load_branches()
        self.commits = self.load_project_commits()
        self.load_individual_commits()

    def load_branches(self):
        """Return SHAs of commits for branches."""
        url = BRANCHES_URL.format(owner=self.owner, project=self.name)
        branches = grab_json(url)
        if not isinstance(branches, list):
            print("Expected list, got %r, retrying." % branches)
            return self.load_branches()
        return [branch['commit']['sha'] for branch in branches]

    def load_project_commits(self):
        result = []
        url = COMMITS_URL.format(owner=self.owner, project=self.name)
        for branch_SHA in self.branch_SHAs:
            result += grab_json(url, params={'since': since(),
                                             'sha': branch_SHA})
        return result

    def load_individual_commits(self):
        for commit in self.commits:
            if not isinstance(commit, dict):
                print("dict in commit isn't a dict: %r" % commit)
                print("the full list of commits:")
                pprint(self.commits)
                print("Continuing anyway...")
                continue
            the_commit = Commit(commit)
            if self.restrict_to_known_users:
                if the_commit.user not in self.users:
                    continue
            self.users[the_commit.user].add_commit(the_commit)
            self.add_commit(the_commit)

    @property
    def is_active(self):
        return bool(self.num_commits)


class User(TestCommitCounter):
    name = None  # We set that from within the commits.

    def add_commit(self, commit):
        if not self.name:
            self.name = commit.user
        TestCommitCounter.add_commit(self, commit)


def main():
    load_custom_settings()

    users = defaultdict(User)
    projects = []

    for organization in SETTINGS['organizations']:
        url = ORG_REPOS_URL.format(organization=organization)
        repos = grab_json(url)
        project_names = [repo['name'] for repo in repos]
        for project_name in project_names:
            project = Project(organization, project_name, users)
            project.load()
            if project.is_active:
                projects.append(project)

    for (organization, project_name) in SETTINGS['extra_projects']:
        project = Project(organization, project_name, users,
                          restrict_to_known_users=True)
        project.load()
        if project.is_active:
            projects.append(project)

    users = users.values()  # Defaultdict isn't handy anymore here.
    users.sort()
    projects.sort()
    print("""
Test statistics
===============

We want more and better testing. For a quick and dirty quantity
indication ('more'), here are the commits that have the string
'test' in of of the commit's touched filenames.

Period: {period} days.
Github organizations that I queried: {orgs}

Projects sorted by amount of commits with tests
-----------------------------------------------

""".format(period=SETTINGS['days'],
            orgs=', '.join(SETTINGS['organizations'])))
    for project in projects:
        project.print_info()
    print("""

Committers sorted by amount of commits with tests
-------------------------------------------------

""")
    for user in users:
        user.print_info()


if __name__ == '__main__':
    main()
