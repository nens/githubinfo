from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from collections import defaultdict
import datetime
import json
import os

import requests

ORG_REPOS_URL = 'https://api.github.com/orgs/{organisation}/repos'
COMMITS_URL = 'https://api.github.com/repos/{owner}/{project}/commits'
VERBOSE = True  # Just for debugging.

# Settings are global and can be modified by some setup/init method.
SETTINGS = {
    'auth': None,  # Set it to ('username', 'very_secret').
    'days': 7,
    'organisations': [
        'ddsc',
        'lizardsystem',
        'nens',
        ],
    'extra_projects': [
        ('buildout', 'buildout'),
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


def grab_json(url, params=None):
    """Return json from URL, including handling pagination."""
    auth = SETTINGS['auth']
    if isinstance(auth, list):
        auth = tuple(auth)
    req = requests.get(url, auth=auth, params=params)
    result = req.json()
    if req.links.get('next'):
        # Paginated content, so we want to grab the rest.
        url = req.links['next']['url']
        # The assumption is "paginated content means it is a list".
        result += grab_json(url, params=params)
    return result


def is_testfile(filepath):
    if 'testsettings.py' in filepath:
        # This one almost always doesn't have anything to do with
        # an added test.
        return False
    if 'test' in filepath:
        return True
    return False


class Commit(object):
    """Wrapper around a commit dict from github's API."""

    def __init__(self, the_dict):
        self.num_testfiles_changed = 0
        self.user = the_dict['commit']['committer']['name']
        commit_url = the_dict['url']
        commit_info = grab_json(commit_url)
        for changed_file in commit_info.get('files', []):
            if is_testfile(changed_file['filename']):
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
        self.commits = self.load_project_commits()
        self.load_individual_commits()

    def load_project_commits(self):
        url = COMMITS_URL.format(owner=self.owner, project=self.name)
        return grab_json(url, params={'since': since()})

    def load_individual_commits(self):
        for commit in self.commits:
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
    # TODO: update settings.
    if os.path.exists('settings.json'):
        custom_settings = json.loads(open('settings.json').read())
        SETTINGS.update(custom_settings)

    users = defaultdict(User)
    projects = []

    for organisation in SETTINGS['organisations']:
        url = ORG_REPOS_URL.format(organisation=organisation)
        repos = grab_json(url)
        project_names = [repo['name'] for repo in repos]
        for project_name in project_names:
            project = Project(organisation, project_name, users)
            project.load()
            if project.is_active:
                projects.append(project)

    for (organisation, project_name) in SETTINGS['extra_projects']:
        project = Project(organisation, project_name, users,
                          restrict_to_known_users=True)
        project.load()
        if project.is_active:
            projects.append(project)

    users = users.values()  # Defaultdict isn't handy anymore here.
    users.sort()
    projects.sort()
    print("""
Nelen & Schuurmans test statistics
==================================

We want more and better testing. For a quick and dirty quantity
indication ('more'), here are the commits that have the string
'test' in of of the commit's touched filenames.

Period: {period} days.
Github organisations that I queried: {orgs}

Projects sorted by amount of commits with tests
-----------------------------------------------

""".format(period=SETTINGS['days'],
            orgs=', '.join(SETTINGS['organisations'])))
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
