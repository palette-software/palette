import os
from setuptools import setup, find_packages

VERSION='0.1'

setup(name='controller',
      version=VERSION,
      author='Palette Software',
      author_email='info@akirisolutions.com',
      url='http://www.palette-software.com',
      scripts = ["bin/controller"],
      data_files = [ "etc/controller.ini",
                     "etc/init/controller.conf",
                     "etc/postfix/main.cf"
                   ],
      packages=['controller'])
