from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest
import mock

import githubinfo.commits


class CommitTest(unittest.TestCase):

    def test_smoke(self):
        self.assertTrue(githubinfo.commits)
