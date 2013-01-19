from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='netHUD',
      version=version,
      description="mustached octo dangerzone",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='ryansb, rossdylan, oddshocks, and qalthos',
      author_email='',
      url='nethud.ryansb.com',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'twisted',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      nethud_tee = nethud:run_tee
      """,
      )
