Github test commit reports for teams
==========================================

.. image:: https://travis-ci.org/nens/githubinfo.png?branch=master
   :target: https://travis-ci.org/nens/githubinfo

Githubinfo is a script that queries the github API of one or more
organizations and gives you a quick report on the amount of commits **with
tests** in the last week.

It is adjustable, of course, which is necessary as I put some company defaults
in there :-)

It is just a simple single command and the output looks like this::

    $ testcommitinfo
    loading project neerslagradar-site
    loading project ...
    ...

    We want more and better testing. For a quick and dirty quantity
    indication ('more'), here are the commits that have the string
    'test' in of of the commit's touched filenames.

    Period: 8 days.
    Github organizations that I queried: ddsc, lizardsystem, nens

    Projects sorted by amount of commits with tests
    -----------------------------------------------

    lizard-neerslagradar: 11 (25%)
    lizard-progress: 3 (9%)
    radar: 1 (33%)
    ...

    Committers sorted by amount of commits with tests
    -------------------------------------------------

    Reinout van Rees: 12 (11%)
    Remco Gerlich: 3 (6%)
    Arjan Verkerk: 2 (8%)
    ...

You can pass ``-h`` or ``--help`` to get usage information, for instance on
how to increase the log level or on how to get the version number.


Goal
----

I wrote it because we wanted to improve our development process at `Nelen &
Schuurmans <http://www.nelen-schuurmans.nl>`_. We wanted more tests. So I
wrote a script:

- It queries the github API for one or more organizations (or personal
  accounts).

- It queries the projects in there for commmits in the last week
  (configurable).

- For every commit, it simply looks if there's a filename in the commit with
  ``test`` in its full path. If so, the commit counts as a "test commit".

- For every project, it counts the number of commits and the number of test
  commits.

- The same for every committer.

At the end, you get a list of projects and committers sorted by number of
commits.


Risk: you get what you measure
------------------------------

The metric is incomplete and imprecise. The same people that start grabbing
their torches and pitchforks when someone mentions "code coverage" will start
grabbing them now. My answer: bugger off.

- You identify colleagues that never ever bother to test. You get to educate
  them. Can I borrow that pitchfork, please?

- You identify projects that have improved in quality.

- You identify projects that were obviously troubled by a deadline and that
  might bite you later on if you have to use them yourself.

- You identify colleagues that bring quality to your project if you work with
  them.

There are a lot of things you don't measure. But someone who doesn't bother
with tests also isn't going to bother adding a whiteline somewhere in a test
file to get at least some test commit credited to his name :-)


Configuration
-------------

Here are the default settings, obviously very my-company-centric::

    SETTINGS = {
        'auth': None,  # Set it to ['username', 'very_secret'].
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

To customize it, add a ``settings.json`` file in your working
directory. Whatever you put in there is used to override the default
``SETTINGS`` dictionary. Make sure it is properly json-formatted, so with
double quotes around strings. Something like this::

    {"auth": ["reinout", "nogal_geheim"],
     "days": 8,
     "organizations": ["lizardsystem"],
     "extra_projects": []}

auth
    username/password list. For when you need access to some private
    projects. Note that you also get a much higher API usage limit when you're
    logged in.

days
    Number of days to report on. By default a week.

organizations
    List of github organizations or personal accounts to query. This is the
    first part after ``github.com`` in URLs like
    ``https://github.com/organization/project``.

extra_projects
    Optional list of ``["organization", "project"]`` lists. For those handful
    of extra projects outside of your organization that one or more colleagues
    do a lot of work on and that are essential to you. I'm listing zc.buildout
    and zest.releaser in here, for instance.

    Note that only the committers that committed to your own organization get
    counted for these extra_projects. This way the list doesn't get polluted.

To verify your settings, you can call ``testcommitinfo --show-config`` which
will print the configuration as testcommitinfo sees it.


Integration with your own systems
---------------------------------

Perhaps you want to include the output in some dashboard? Or you want to
generate a nice HTML out of it?

For those use cases, you can export a JSON file with the collected project and
user information. Pass a JSON filename with the ``--json-output`` commandline
option and you'll have everything you need.


Problems?
---------

Sometimes the github API fails intermittently. There are some "try it a second
time" if/elses in the code which work around most of the issues. Every time I
discover an additional problem, I add some code to work around it.

So if you've got a problem, you could just try running it a second time, most
often that works just fine.

If you've got a real bug, you could ask me (`reinout@vanrees.org
<mailto:reinout@vanrees.org>`_) to take a look. Or, better, submit a issue on
https://github.com/nens/githubinfo/issues . Or, even better, try to fix it in
a pull request.
