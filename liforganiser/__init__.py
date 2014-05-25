#!/usr/bin/env python3

"""Provides an API to scrape the course, chapter and lesson data from
LearnItFirst.com and then organise, move and rename pre-downloaded course
chapters accordingly.

The package exports no further modules but it contains an empty course_data
folder which will be populated with JSON files containing course data dumps
for ease of future access.

This module exports the following two names only:
Exception LearnItFirstError -- General error class, predominantly pertaining
    to issues encountered when scraping data from LearnItFirst.com.
class Course -- The one and only access point for scraping data and organising
    pre-downloaded course chapters.

View each name's docstring for more verbose information.

To see prettified help information on command line usage, please call the
script without arguments.
"""

from urllib import parse
# TODO: import argparse.
import json
import logging
import os
import re
import shutil
import stat
import zipfile

import bs4
import requests


# Linux is pretty lenient compared with Windows and only seems to forbid the
# use of / in file names.
_CHAR_REPLACEMENTS = {
    "/": " & ",
    " - ": "; "
}
_JSON_DIR_PATH = os.path.join(os.path.dirname(__file__), "course_data")
if not os.path.isdir(_JSON_DIR_PATH):
    os.mkdir(_JSON_DIR_PATH)
_JSON_PATH_FORMAT = os.path.join(_JSON_DIR_PATH, "%s" + os.extsep + "json")
# Declare variable for readable line length.
_log_path = os.path.join(os.path.dirname(__file__), "output" + os.path.extsep +
                         "log")
_format = "%(asctime)s (%(levelname)s) -> %(message)s"
logging.basicConfig(filename=_log_path, format=_format,
                    datefmt="%d/%m/%Y %H:%M:%S")
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_stderr_handler = logging.StreamHandler()
_stderr_handler.setFormatter(logging.Formatter(_format, "%H:%M:%S"))
_DEFAULT_LEVEL = logging.INFO
_logger.addHandler(_stderr_handler)
_ABSENT = object()


class LearnItFirstError(Exception):
    """General error class, predominantly pertaining to issues encountered when
    scraping data from LearnItFirst.com.
    """


class Course(object):
    """Obtains the data for the course including it's chapters and lessons, to
    then be used to organise, rename and move pre-downloaded course chapters
    accordingly.

    Keyword arguments:
    course_id -- the unique ID integer (between 100 and 999) of the course
    title -- the full name of the title without it's ID
    chapters -- a list of Chapter objects
    stderr_level_override -- an integer value representing the minimum level of
        logging verbosity in accordance with logging levels.  If no value is
        passed, logging.INFO (20) will be used (default None)

    The instance variables are as follows:
    self.course_id -- as above
    self.title -- as above
    self.chapters -- as above

    The other public methods are as follows:
    classmethod from_url -- Scrape course data from LearnItFirst.com and return
        a Course instance with this data.  Ordinarily, this would be called
        implicitly via the get() method.  Only call explicitly if you have
        reason to believe that the existing JSON file is corrupt or out of date
        with course data on LearnItFirst.com
    classmethod get -- Return a Course object with course data for the relevant
        course ID.  If the JSON file exists, get data from here ahead of
        scraping LearnItFirst.com
    method dump -- Dump course data to a JSON file inside ./course_data/
    method organise -- Organise, move and rename all relevant course chapters
        including their lessons from within a source directory.
    """

    def __init__(self, course_id, title, chapters,
                 stderr_level_override=None):
        self.course_id = course_id
        self.title = title
        self.chapters = chapters
        if stderr_level_override is not _ABSENT:
            _stderr_handler.setLevel(stderr_level_override or _DEFAULT_LEVEL)

    @classmethod
    def _remove_readonly(cls, func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    @classmethod
    def _transform_name(cls, num, name, course_id=None, chapter_num=None):
        for char in _CHAR_REPLACEMENTS:
            name = name.replace(char, _CHAR_REPLACEMENTS[char])
        if chapter_num is not None:
            return ("s%03dch%02dl%02d - %s" % (course_id, chapter_num, num,
                                               name))
        return "%02d - %s" % (num, name)

    @classmethod
    def _from_json(cls, course_id, stderr_level_override):
        with open(_JSON_PATH_FORMAT % course_id) as fp:
            _logger.debug("Reading JSON file and loading the data into a "
                          "python dict")
            course = json.load(fp)
        chapters = {}
        try:
            course_chapters = course["chapters"]
            for chapter_num in course_chapters:
                chapter = course_chapters[chapter_num]
                chapter_num = int(chapter_num)
                lessons = {}
                chapter_lessons = chapter["lessons"]
                for lesson_num in chapter_lessons:
                    # Declare variable for readable line length.
                    lesson = chapter_lessons[lesson_num]
                    lesson_num = int(lesson_num)
                    lessons[lesson_num] = _Lesson(lesson_num, lesson)
                chapters[chapter_num] = _Chapter(chapter_num, chapter["name"],
                                                 lessons)
        except (KeyError, IndexError, TypeError) as message:
            _logger.warning("The JSON file format is different to what was "
                            "expected and has probably been tampered with. An "
                            "error was encountered; %s" % message)
            return
        _logger.info("Data for course ID, %s, was successfully loaded "
                     "from the JSON file" % course_id)
        return Course(course["course_id"], course["title"], chapters,
                      stderr_level_override)

    @classmethod
    def from_url(cls, course_id, stderr_level_override=None):
        """Scrape course data from LearnItFirst.com and return
        a Course instance with this data.  Ordinarily, this would be called
        implicitly via the get() method.  Only call explicitly if you have
        reason to believe that the existing JSON file is corrupt or out of date
        with course data on LearnItFirst.com.

        Keyword arguments:
        course_id -- the unique ID integer (between 100 and 999) of the course
        stderr_level_override -- an integer value representing the minimum
            level of logging verbosity in accordance with logging levels.  If
            no value is passed, logging.INFO (20) will be used (default None)
        """
        _logger.debug("Attempting to get data for course ID, %s, by scraping "
                      "LearnItFirst.com" % course_id)
        if stderr_level_override is not _ABSENT:
            _stderr_handler.setLevel(stderr_level_override or _DEFAULT_LEVEL)
        headers = {"User-Agent": "Chromium/Linux"}
        url = "http://www.learnitfirst.com/Course/%s/default.aspx" % course_id
        _logger.debug("Making a HTTP request with custom headers as the "
                      "website block's requests coming from a "
                      "programattic-looking User-Agent")
        try:
            request = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as message:
            _logger.error("An error was encountered when making the HTTP "
                          "request; %s" % message)
        if request.status_code == requests.codes.not_found:
            _logger.critical("The course ID, %s, does not exist on "
                             "LearnItFirst.com. An exception will be raised." %
                             course_id)
            raise LearnItFirstError("course ID, %s, does not exist on "
                                    "LearnItFirst.com" % course_id)
        try:
            soup = bs4.BeautifulSoup(request.text, "lxml")
        except bs4.FeatureNotFound as message:
            _logger.critical("The html cannot be parsed. An error was "
                             "encountered; %s" % message)
            raise bs4.FeatureNotFound(message)
        course_title = cls._transform_name(course_id,
                                           soup.find("h1").string.strip())
        for link in soup.find_all("a"):
            string = link.string
            if string is not None:
                if string.strip() == "View the videos in this course":
                    url = parse.urljoin(url, link["href"])
                    break
        else:
            _logger.critical("The website structure or link text to the "
                             "TheBigList.aspx page has changed and the data "
                             "cannot be found. An exception will be raised.")
            raise LearnItFirstError("the website structure or link text to "
                                    "the TheBigList.aspx page has changed")
        soup = bs4.BeautifulSoup(requests.get(url, headers=headers).text,
                                 "lxml")
        chapters = {}
        chapter_divs = soup.find_all("div", "chapterTitle")
        if not chapter_divs:
            _logger.critical("The TheBigList.aspx page has changed structure "
                             "and chapter data cannot be scraped. An "
                             "exception will be raised.")
            raise LearnItFirstError("The TheBigList.aspx page has changed "
                                    "structure and chapter data cannot be "
                                    "scraped.")
        for chapter_div in chapter_divs:
            # Declare variable for readable line length.
            string = chapter_div.h2.b.string.strip()
            chapter_num = int(re.match(r"Chapter\s+(\d+):", string).group(1))
            # Declare variable for readable line length.
            raw_name = chapter_div.h2.a.string.strip()
            chapter_name = cls._transform_name(chapter_num, raw_name)
            lessons = {}
            # Declare variable for readable line length.
            next_div = chapter_div.find_next_sibling("div")
            lesson_divs = next_div.find_all("div", "chapterBorder")
            if not lesson_divs:
                _logger.critical("The TheBigList.aspx page has changed "
                                 "structure and lesson data cannot be "
                                 "scraped.  An exception will be raised.")
                raise LearnItFirstError("The TheBigList.aspx page has changed "
                                        "structure and lesson data cannot be "
                                        "scraped.")
            for lesson_div in lesson_divs:
                # Declare variable for readable line length.
                start_slice = len("%s." % chapter_num)
                first_div, second_div = lesson_div.find_all("div", limit=2)
                lesson_num = int(first_div.string.strip()[start_slice:])
                raw_name = second_div.a.string.strip()
                lesson_name = cls._transform_name(lesson_num, raw_name,
                                                  course_id, chapter_num)
                lessons[lesson_num] = _Lesson(lesson_num, lesson_name)
            chapters[chapter_num] = _Chapter(chapter_num, chapter_name,
                                             lessons)
        _logger.info("Data for course ID, %s, was successfully scraped from "
                     "LearnItFirst.com" % course_id)
        course = Course(course_id, course_title, chapters, _ABSENT)
        course.dump()
        return course

    @classmethod
    def get(cls, course_id, stderr_level_override=None):
        """Return a Course object with course data for the relevant
        course ID.  If the JSON file exists, get data from here ahead of
        scraping LearnItFirst.com.

        Keyword arguments:
        course_id -- the unique ID integer (between 100 and 999) of the course
        stderr_level_override -- an integer value representing the minimum
            level of logging verbosity in accordance with logging levels.  If
            no value is passed, logging.INFO (20) will be used (default None)
        """
        _stderr_handler.setLevel(stderr_level_override or _DEFAULT_LEVEL)
        _logger.debug("Searching for an existing JSON file for data for the "
                      "course ID, %s." % course_id)
        json_file_path = _JSON_PATH_FORMAT % course_id
        if os.path.isfile(json_file_path):
            _logger.debug("Existing JSON file found at %s" % json_file_path)
            result = cls._from_json(course_id, _ABSENT)
            if result is not None:
                return result
        course = cls.from_url(course_id, _ABSENT)
        return course

    def dump(self):
        """Dump course data to a JSON file inside ./course_data/"""
        course = {
            "course_id": self.course_id,
            "title": self.title,
            "chapters": {}
        }
        for chapter_num in self.chapters:
            chapter = self.chapters[chapter_num]
            course["chapters"][chapter.num] = {
                "name": chapter.name,
                "lessons": {lesson_num: lesson_data.name for lesson_num,
                            lesson_data in chapter.lessons.items()}
            }
        with open(_JSON_PATH_FORMAT % self.course_id, "w+") as fp:
            _logger.debug("Dumping the data into a JSON file so that it can "
                          "be accessed at a later time quickly and without "
                          "need to scrape LearnItFirst.com, saving time and "
                          "unnecessary requests.")
            json.dump(course, fp)

    def organise(self, src, dst, chapter_pattern, lesson_pattern, avi_dst=None,
                 pdf_dst=None, completed_prefix=None, ignored_exts=("html",)):
        """Organise, move and rename all relevant course chapters including
        their lessons from within a source directory.

        Keyword arguments:
        src -- the full path to the source directory containing the course
            chapter directories or zip files
        dst -- the full path to the destination directory which all valid,
            lesson-related files will be moved to by default
        chapter_pattern -- a regex pattern representing a valid chapter name.
            Bear in mind that both directories and zip files should likely be
            accepted
        lesson_pattern -- a regex pattern representing a valid lesson file that
            should be matched to scraped course data and renamed accordingly
        avi_dst -- the full path to the destination directory in which AVI
            files only should be moved to (default None)
        pdf_dst -- the full path to the destination directory in which PDF
            files only should be moved to (default None)
        completed_prefix -- a prefix to be prepended to the old directories /
            zip files in which the contents have been succesfully moved, so
            that re-calling organise will not match and attempt to organise
            them again (default None)
        ignored_exts -- an iterable containing extension names (without the
            seperator) that should be ignored when renaming and moving files
            (default ("html", ))
        """
        if not os.path.isdir(src):
            _logger.critical("Invalid or non-existent source directory, %s." %
                             src)
            raise OSError("invalid / non-existent source directory, %s" % src)
        if not os.path.isdir(dst):
            _logger.critical("Invalid or non-existent destination directory, "
                             "%s." % dst)
            raise OSError("invalid / non-existent destination directory, %s" %
                          dst)
        if avi_dst is None:
            avi_dst = dst
        elif not os.path.isdir(avi_dst):
            _logger.critical("Invalid or non-existent AVI destination "
                             "directory, %s." % avi_dst)
            raise OSError("invalid / non-existent AVI destination directory, "
                          "%s" % avi_dst)
        if pdf_dst is None:
            pdf_dst = dst
        elif not os.path.isdir(pdf_dst):
            _logger.critical("Invalid or non-existent PDF destination "
                             "directory, %s." % pdf_dst)
            raise OSError("invalid / non-existent PDF destination directory, "
                          "%s" % pdf_dst)
        temp_dir_path = os.path.join(src, ".temp")
        _logger.debug("Searching for valid chapter directories for course ID, "
                      "%s." % self.course_id)
        for name in os.listdir(src):
            original_path = os.path.join(src, name)
            chapter_match = re.match(chapter_pattern, name)
            if not chapter_match:
                continue
            _logger.debug("A valid chapter directory has been found at %s." %
                          original_path)
            chapter_num = int(chapter_match.group(1))
            if zipfile.is_zipfile(original_path):
                if not os.path.isdir(temp_dir_path):
                    _logger.info("Temporary directory being created for "
                                 "extracted zipfiles, %s." % temp_dir_path)
                    os.mkdir(temp_dir_path)
                path = os.path.join(temp_dir_path, name)
                _logger.info("Chapter number, %s, was found to be a zipfile "
                             "and is being extracted. This may take a "
                             "while..." % chapter_num)
                zipfile.ZipFile(original_path).extractall(path)
            elif os.path.isfile(original_path):
                continue
            else:
                path = original_path
            chapter = self.chapters[chapter_num]
            files = []
            contents_path = None
            _logger.debug("Searching for valid lesson files for chapter, %s." %
                          chapter_num)
            for root, dir_names, file_names in os.walk(path):
                if not file_names:
                    continue
                if contents_path is None:
                    contents_path = root
                for file_name in file_names:
                    split_ext = os.path.splitext(file_name)
                    if len(split_ext) > 1:
                        ext = split_ext[1][1:].lower()
                        if ext in ignored_exts:
                            continue
                    else:
                        ext = ""
                    file_path = os.path.join(root, file_name)
                    dst_rel_path = os.path.join(self.title, chapter.name)
                    if root != contents_path:
                        # Declare variable for readable line length.
                        rel_path = os.path.relpath(root, contents_path)
                        dst_rel_path = os.path.join(dst_rel_path, rel_path)
                    lesson_match = re.match(lesson_pattern, file_name)
                    if lesson_match is not None:
                        _logger.debug("A valid lesson file that matches the "
                                      "file name format has been found at %s."
                                      % file_path)
                        num = int(lesson_match.group(1))
                        if ext in ("avi", "pdf"):
                            lesson = chapter.lessons.get(num)
                            if lesson is None:
                                _logger.error("Lesson number, %s, does not"
                                              "exist on LearnItFirst.com. "
                                              "This chapter will be skipped; "
                                              "lessons cannot be renamed with "
                                              "confidence as a missing lesson "
                                              "file could point to a mix up "
                                              "in the other lesson names." %
                                              num)
                                break
                            name = lesson.name + os.path.extsep + ext
                            if ext == "avi":
                                print("dst_rel_path = %s" % dst_rel_path)
                                new_file_path = os.path.join(avi_dst,
                                                             dst_rel_path,
                                                             name)
                                print("new_file_path = %s" % new_file_path)
                            elif ext == "pdf":
                                new_file_path = os.path.join(pdf_dst,
                                                             dst_rel_path,
                                                             name)
                        else:
                            description = lesson_match.group(2).strip()
                            if not description:
                                _logger.warning("file name, %s, contains no "
                                                "description and so renamed "
                                                "file will be non-descript" %
                                                file_name)
                            name = (self._transform_name(num, description,
                                                         self.course_id,
                                                         chapter_num) +
                                    os.path.extsep + ext)
                            new_file_path = os.path.join(dst, dst_rel_path,
                                                         name)
                    else:
                        _logger.debug("A file has been found that does not "
                                      "match the lesson file name format. It "
                                      "will still be moved but not renamed.")
                        num = None
                        new_file_path = os.path.join(dst, dst_rel_path,
                                                     file_name)
                    files.append(_File(ext, num, file_path, new_file_path))
            if set(chapter.lessons) != set(_file.num for _file in
                                           files if _file.ext == "avi" and
                                           _file.num is not None):
                _logger.error("The video contents for chapter number, %s, are "
                              "different to what is listed on "
                              "LearnItFirst.com. This chapter will be "
                              "skipped." % chapter_num)
                continue
            for _file in files:
                _logger.info("Moving and renaming %s to %s" %
                             (_file.file_path, _file.new_file_path))
                # Use shutil in case the user is moving files to a new file
                # system, i.e. an external HDD.
                dir_path = os.path.dirname(_file.new_file_path)
                if not os.path.isdir(dir_path):
                    os.makedirs(dir_path)
                shutil.move(_file.file_path, _file.new_file_path)
            if completed_prefix is not None:
                head, tail = os.path.split(original_path)
                _logger.debug("Prepending \"DONE\" to chapter number, %s's "
                              "old zip file / directory to stop it from being "
                              "analysed if  organise() is re-called." %
                              chapter_num)
                os.rename(original_path, os.path.join(head, completed_prefix +
                                                      tail))
        if os.path.isdir(temp_dir_path):
            _logger.info("Deleting the temporary directory tree at %s." %
                         temp_dir_path)
            shutil.rmtree(temp_dir_path, onerror=self._remove_readonly)


class _Chapter(object):
    def __init__(self, num, name, lessons):
        self.num = num
        self.name = name
        self.lessons = lessons


class _File(object):
    def __init__(self, ext, num, file_path, new_file_path):
        self.ext = ext
        self.num = num
        self.file_path = file_path
        self.new_file_path = new_file_path


class _Lesson(object):
    def __init__(self, num, name):
        self.num = num
        self.name = name
