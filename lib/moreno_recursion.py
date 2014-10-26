import itertools
from lib.time_align import ActivationsBetween, best_partial_score_table, best_alignment
from lib import asr
from lib.subtitles.remove_fluff import corpusize


class AlignmentInfo:
    def __init__(self, activations, texts, text_lengths, directory, syllable_duration, segment_seconds, window, min_len, use_fmllr, use_automaton, per_transcription_compile):
        self._activations = activations
        self._total_length = activations.shape[0]
        self._num_subs = len(texts)
        self._texts = [corpusize(text) for text in texts]
        self._text_lengths = text_lengths
        self._directory = directory
        self._syllable_duration = syllable_duration
        self._segment_seconds = segment_seconds
        self._window = window
        self._min_len = min_len
        self._use_fmllr = use_fmllr
        self._use_automaton = use_automaton
        self._per_transcription_compile = per_transcription_compile

    def get_alignment(self, passes=5):
        anchors = []
        for i in xrange(1, passes):
            anchors = self.anchor_pass(anchors)
        return [start for sub_num, start in self.anchor_pass(anchors, True)]

    def anchor_pass(self, anchors=[], final_pass=False):
        anchors = [(-1, 0, 0)] + anchors + [(self._num_subs, self._total_length, 0)]

        alignment = []
        for (start_anchor, end_anchor) in itertools.izip(anchors, itertools.islice(anchors, 1, None)):
            start_text, start_time, start_length = start_anchor
            first_text = start_text + 1
            first_time = start_time + start_length
            end_text, end_time, _ = end_anchor

            activations = self._activations[first_time:end_time]
            text_lengths = self._text_lengths[first_text:end_text]

            alignment += [(sub + first_text, start + first_time) for sub, start in get_alignment(activations, text_lengths)]
            alignment.append((end_text, end_time))

        if final_pass:
            return alignment[:-1]

        anchors = asr.get_anchors(self._directory, self._total_length / 10, alignment[:-1], self._texts, self._syllable_duration, self._segment_seconds, self._window, self._min_len, self._use_fmllr, self._use_automaton, self._per_transcription_compile)
        return [(sub, time, self._text_lengths[sub]) for sub, time in anchors]


def get_alignment(activations, text_lengths):
    if len(text_lengths) == 0 or activations.shape[0] == 0:
        return []
    activations_between = ActivationsBetween(activations)
    alignment = best_alignment(best_partial_score_table(text_lengths, activations_between), text_lengths, activations_between)
    return list(enumerate(alignment))
