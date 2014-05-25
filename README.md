LIFOrganiser
============

Provides an API to scrape the course, chapter and lesson data from LearnItFirst.com and then organise, move and rename pre-downloaded course chapters accordingly.


## Description
>LearnItFirst.com hosts hundreds of hours of video tutorials that make up full certification courses about everything SQL. Subscribers must download the course contents chapter by chapter. The downloaded chapters contain the lesson files (AVI videos, PDF presentation slides and supplementary content & exercises). 

However, they are named fairly non-descriptively compared with the disciplined naming convention on the website's course listings. This python package sets out to solve that problem as well as automatically unzipping all the downloaded chapters within a course and organising the video & supplementary content. The module produces contains extensive logging and the code is fully documented and it can be feely distributed and modified under the Apache License v2.


## Installation
1. [Download ZIP](https://github.com/adamcunnington/LIFOrganiser/archive/master.zip) & Unzip or ```git clone https://github.com/adamcunnington/LIFOrganiser.git```
2. CD into LIFOrganiser
3. ```python setup.py install```

You may need administrator privileges for step 3. What you do here depends on your operating system. For example in Ubuntu you would say sudo ```python setup.py install``` To bypass the need for administrator privileges, you may be able to make use of the ```--user``` flag. In this way you can install the package only for the current user.

For more information, see:
* [Python 3.4 Documentation: Installing Python Modules](https://docs.python.org/3.4/install/index.html)
* [Python 2.7 Documentation: Installing Python Modules](https://docs.python.org/2.7/install/index.html)


## Usage
```python
import liforganiser

_src = "/home/ac/Downloads"
_dst = "/home/ac/Dropbox/Documents/Education/Tutorials/LearnItFirst"
_avi_dst = "/media/ADAM-PC/Tutorials/LearnItFirst"

ssas = liforganiser.Course.get(165)
ssas.organise(_src, _dst, chapter_pattern=r"SSAS2008_Chapter(\d+)(?:.zip|)",
              lesson_pattern=r"Ch\d+_(\d+)(?:_|)([^\.]*)(?:\.\w+|)",
              avi_dst=_avi_dst, completed_prefix="DONE")
              
ssis = liforganiser.Course.get(158)
ssis.organise(_src, _dst, chapter_pattern=r"SSIS2008_Chapter(\d+)(?:.zip|)",
              lesson_pattern=r"\d+_(\d+)(?:-|)([^\.]*)(?:\.\w+|)",
              avi_dst=_avi_dst, completed_prefix="DONE")
              
tsql = liforganiser.Course.get(158)
tsql.organise(_src, _dst, chapter_pattern=r"TSQL2008_Chapter(\d+)(?:.zip|)",
              lesson_pattern=r"Ch\d+_(\d+)(?:_|)([^\.]*)(?:\.\w+|)",
              avi_dst=_avi_dst, completed_prefix="DONE")
```

## Video Demonstration
Coming soon.
