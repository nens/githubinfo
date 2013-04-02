Changelog of githubinfo
===================================================


1.1 (2013-04-02)
----------------

- Added optional export of the results to a JSON file. Useful if you want to
  format the output yourself, for instance to create a HTML page.

- Added argument parsing via argparse. **Warning**: this requires python 2.7
  at a minimum. I guess that's not a problem. At least ``-h`` now gives a
  proper usage message!

- Added ``githubinfo.__version__`` attribute.


1.0.1 (2013-04-02)
------------------

- Small README fix: quote error in example config file. Thanks Maximilien
  Riehl for noticing it!


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
