#!/usr/bin/env python3

from setuptools import setup


def get_readme():
    with open("README.md") as f:
        return f.read()


setup(name="LIFOrganiser",
      version="1.0",
      description="LearnItFirst.com Course Contents Organiser",
      long_description=get_readme(),
      author="Adam Cunnington",
      author_email="ac@adamcunnington.info",
      license="GPLv3",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Education",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.0",
          "Programming Language :: Python :: 3.1",
          "Programming Language :: Python :: 3.2",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Topic :: Education"],
      keywords="LearnItFirst Course Organiser File-Renamer",
      packages="liforganiser",
      install_requires=[
          "BeautifulSoup4",
          "requests"])
