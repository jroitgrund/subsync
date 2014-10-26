import numpy
import sys


class ActivationsBetween:
    def __init__(self, activations):
        self._activations = activations
        self._end = activations.shape[0]
        self._init_before_after()

    def _init_before_after(self):
        before = 0
        after = self._activations.sum()
        self._before = numpy.zeros(self._end + 1, dtype=numpy.int)
        self._after = numpy.zeros(self._end + 1, dtype=numpy.int)
        self._before[0] = before
        self._after[0] = after
        for i, activation in enumerate(self._activations):
            before += activation
            after -= activation
            self._before[i + 1] = before
            self._after[i + 1] = after

    def _pos_in_range(self, pos):
        return max(min(pos, self._end), 0)

    def end(self):
        return self._end

    def before(self, pos):
        return self._before[self._pos_in_range(pos)]

    def after(self, pos):
        return self._after[self._pos_in_range(pos)]

    def between(self, start, end):
        return self.before(end) - self.before(start)


def best_partial_score_table(mobile_segments, activations_between):
    size = max(activations_between.end(), sum(mobile_segments) + 20)
    partial_score_table = numpy.zeros((len(mobile_segments), size), dtype=numpy.int)
    total_length = 0
    for i, length in enumerate(mobile_segments):
        total_length += length
        _scores_with_segment(partial_score_table, i, length, activations_between, total_length)
    return partial_score_table


def _scores_with_segment(partial_score_table, index, length, activations_between, total_length):
    num_positions = partial_score_table.shape[1]
    best_so_far = -(sys.maxint - 1)
    for highest_time in range(0, num_positions):
        if highest_time < total_length:
            score = -(sys.maxint - 1)
        else:
            start = highest_time - length + 1
            score = partial_score_table[index - 1, start - 1] if start > 0 and index > 0 else 0
            if score != -(sys.maxint - 1):
                score += activations_between.between(start, start + length)
        if score > best_so_far:
            best_so_far = score
        partial_score_table[index, highest_time] = best_so_far


def best_alignment(partial_score_table, mobile_segments, activations_between):
    numpy.savetxt('score_table.txt', partial_score_table, delimiter='\t')
    num_segments, num_positions = partial_score_table.shape
    alignment = numpy.zeros(num_segments, dtype=numpy.int)
    necessary_score = partial_score_table[-1, -1]
    start_time = 0
    for segment in xrange(num_segments - 1, -1, -1):
        end_time = numpy.nonzero(partial_score_table[segment, ] == necessary_score)[0][0] + 1
        length = mobile_segments[segment]
        start_time = end_time - length
        alignment[segment] = max(-1, start_time)
        if start_time < 0:
            print "start time %s for segment %s" % segment
        necessary_score -= activations_between.between(start_time, start_time + length)
        if necessary_score == 0:
            break
    assert necessary_score == 0
    return alignment
