import os


def encode(dir_name):
    for root, dir_names, file_names in os.walk(dir_name):
        for file_name in file_names:
            split_ext = os.path.splitext(file_name)
            if len(split_ext) > 1 and split_ext[-1][1:].lower() == "avi":
                os.system("mencoder \"%s\" -o \"%s\" -oac mp3lame -ovc x264" %
                          (os.path.join(root, file_name),
                           os.path.join(root, split_ext[0] + os.path.extsep +
                                        "mp4")))

"""
mencoder "c160ch01l03 - Why this Course is So Important: Is It the Greatest Course Ever?.avi" -o "c160ch01l03 - Why this Course is So Important: Is It the Greatest Course Ever?.mp4" -oac mp3lame -ovc x264
avconv -i "c160ch01l03 - Why this Course is So Important: Is It the Greatest Course Ever?.avi" -c:a mp3 -c:v mpeg4 "c160ch01l03 - Why this Course is So Important: Is It the Greatest Course Ever?.mp4"
"""
