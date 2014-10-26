
import codecs


class SyllableCounter:
    def __init__(self):
        self._wordlist = []
        with codecs.open('data/mhyph.txt', encoding='utf-8') as mhyph:
            for word in mhyph:
                syllables = word.count(u"\u00A5") + 1
                self._wordlist.append((word.replace(u"\u00A5", '').replace('\n', '').lower(), syllables))

    def count_syllables(self, word):
        word = word.lower()
        return next((syllables for candidate, syllables in self._wordlist if word == candidate),
                    int(round(len(word) / 3.0)))


def text_lengths(text_segments, voice_duration):
    syllable_counter = SyllableCounter()
    segment_syllables = [sum(syllable_counter.count_syllables(word) for word in segment.split()) for segment in text_segments]
    total_syllables = sum(segment_syllables)
    syllable_duration = voice_duration / float(total_syllables)
    text_lengths = [int(round(syllables * syllable_duration)) for syllables in segment_syllables]
    return text_lengths, syllable_duration
