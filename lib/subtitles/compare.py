import itertools
import numpy


def simple_compare(subs1, subs2):
    a = [_begin_diff(sub1, sub2) for sub1, sub2 in itertools.izip(subs1, subs2)]
    return max(a), a.index(max(a)), sum(a), numpy.mean(a), len([diff for diff in a if diff > 15]), len([diff for diff in a if diff > 10]), len([diff for diff in a if diff > 5])


def _begin_diff(sub1, sub2):
    return abs((sub1.start - sub2.start).ordinal) / 1000.0


def _time_diff(sub1, sub2):
    return (abs((sub1.start - sub2.start).ordinal) + abs((sub1.end - sub2.end).ordinal)) / 1000.0


def compare(first, second):
    first, second = _word_locations(first), _word_locations(second)
    used_words = dict()
    diff = 0

    for word in first:
        try:
            diff += _difference(first[word], second[word])
        except KeyError:
            diff += _difference(first[word], [])
        used_words[word] = True

    for word in second:
        if word not in used_words:
            diff += _difference(second[word], [])

    return diff


def _word_locations(subs):
    res = dict()
    for sub in subs:
        sub_info = (sub.start, sub.end)
        for word in sub.text.split(' '):
            try:
                res[word].append(sub_info)
            except KeyError:
                res[word] = [sub_info]

    return res


def _difference(positions1, positions2):
    used_pos2 = []
    diff = 0
    for pos1 in positions1:
        try:
            match_overlap, match_index, match_len =\
                max((_overlap(pos1, pos2), index, _len(pos2))
                    for (index, pos2) in
                    enumerate(positions2) if index not in used_pos2)
            used_pos2.append(match_index)
            diff += match_len + _len(pos1) - 2 * match_overlap
        except ValueError:
            diff += _len(pos1)

    diff += sum(_len(pos2) for (index, pos2) in
                enumerate(positions2) if index not in used_pos2)
    return diff


def _overlap(pos1, pos2):
    pos1_start, pos1_end = pos1
    pos2_start, pos2_end = pos2
    last_start, first_end = None, None
    if pos1_start >= pos2_start:
        last_start = pos1_start
    else:
        last_start = pos2_start
    if pos2_start <= pos2_start:
        first_end = pos1_end
    else:
        first_end = pos2_end

    return max(0, (first_end - last_start).ordinal)


def _len(pos):
    return (pos[1] - pos[0]).ordinal
