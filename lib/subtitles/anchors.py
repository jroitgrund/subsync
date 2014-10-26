import itertools
import random


def get_anchors(subtitles, freq):
    if freq == 0:
        return []

    anchors = []
    for sub in itertools.islice(subtitles, None, None, freq):
        words = sub.text.split(' ')
        pos = random.randrange(0, len(words))
        start = sub.start.ordinal
        length = (sub.end - sub.start).ordinal
        time = start + int(length * (pos / float(len(words))))
        if time < start or time > sub.end.ordinal:
            raise AssertionError("this shouldn't be possible")
        anchors.append((words[pos], time))
    return anchors
