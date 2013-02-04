#!/usr/bin/env python 
"""
"""
from setuptools import setup
from distutils.command.build import build as distutils_build
from distutils.cmd import Command
from os.path import join
import sys

VERSION="0.1.0"


# --- Custom distutils commands -----------------------------------------------

class test(Command):

    """Run unit tests."""

    description = "Run unit tests."

    user_options = [('verbosity=', 'V', 'set test report verbosity')]

    def initialize_options(self):
        self.verbosity = 0

    def finalize_options(self):
        try:
            self.verbosity = int(self.verbosity)
        except ValueError:
            raise ValueError('verbosity must be an integer.')

    def run(self):
        print 'MOOO'
        import unittest
        suite = unittest.TestLoader().discover('protvis.test')
        result = unittest.TextTestRunner(verbosity=self.verbosity+1).run(suite)
        print 'Have result it is %s' % result
        if not result.wasSuccessful():            
            sys.exit(1)


setup(name="protvis",
      version=VERSION,
      description="",
      author="",
      packages=["protvis"],
      classifiers=['Programming Language :: Python',
                   'Programming Language :: Python :: 2.7'],
      cmdclass={'test': test})
      
