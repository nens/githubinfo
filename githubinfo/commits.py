from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import datetime

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
        ]
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
    req = requests.get(url, auth=SETTINGS['auth'], params=params)
    result = req.json()
    if req.links.get('next'):
        # Paginated content, so we want to grab the rest.
        url = req.links['next']['url']
        # The assumption is "paginated content means it is a list".
        result += grab_json(url, params=params)
    return result
