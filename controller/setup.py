import os
from setuptools import setup, find_packages

# VERSION='2.0.0'
VERSION=os.environ['CONTROLLER_VERSION']

setup(name='controller',
      version=VERSION,
      author='Palette Software',
      author_email='info@palette-software.com',
      url='http://www.palette-software.com',
      scripts = [],
      data_files = [],
      include_package_data=True,
      package_data={
        '':
          ['*.json']
      },
      packages=find_packages())
