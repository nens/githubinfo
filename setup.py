from setuptools import setup

version = '1.1'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'setuptools',
    'requests >= 1.1.0',
    ],

tests_require = [
    'mock',
    'coverage',
    ]

setup(name='githubinfo',
      version=version,
      description="Extract test-related commit info from github",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords=[],
      author='Reinout van Rees',
      author_email='reinout@vanrees.org',
      url='https://github.com/nens/githubinfo',
      license='GPL',
      packages=['githubinfo'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
            'testcommitinfo = githubinfo.commits:main',
          ]},
      )
