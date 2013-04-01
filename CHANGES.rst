Changelog of githubinfo
===================================================


1.0 (2013-04-01)
----------------

- Added proper documentation and usage instructions to the README.

- Detecting doctests, too. For ``.rst`` and ``.txt`` files, we search for
  ``>>>`` in the commit's patch, that's a pretty good indication of a doctest
  commit. I needed this for detecting my well-tested commits in zc.buildout.

- Loading commits from branches, too.

- Added option for extra projects outside of the main ones. Commits in here
  are only counted if they're from committers to our main organizations.

- Extracting test commit info from github organizations.

- Initial project structure created with nensskel 1.30.dev0.
