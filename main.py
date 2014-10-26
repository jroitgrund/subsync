from lib import syllables
from lib import vad_reader
from lib import moreno_recursion
from lib.subtitles.write_subs import write_srt
import argparse
import numpy
import pysrt
import subprocess
import shlex
import sys


def main():
    print ' '.join(sys.argv)
    parser = argparse.ArgumentParser(
        description="Run synchronization with the data files in a directory")
    parser.add_argument('directory')
    parser.add_argument('-a', action='store_true')
    parser.add_argument('-t', action='store_true')
    parser.add_argument('-f', action='store_true')
    parser.add_argument('-i', action='store_true')
    parser.add_argument('-p', default=2, type=int)
    parser.add_argument('-s', default=30, type=int)
    parser.add_argument('-w', default=1, type=int)
    parser.add_argument('-l', default=5, type=int)
    args = parser.parse_args()
    directory = args.directory
    use_automaton = args.a
    use_own_time = args.t
    use_fmllr = args.f
    per_transcription_compile = args.i
    segment_seconds = args.s
    window = args.w
    min_len = args.l

    passes = args.p
    generate_subs(directory, use_own_time, passes, segment_seconds, window, min_len, use_fmllr, use_automaton, per_transcription_compile)


def generate_subs(directory, use_own_time, passes, segment_seconds, window, min_len, use_fmllr, use_automaton, per_transcription_compile):
    activations = vad_reader.movie_activations(directory)
    if use_own_time:
        voiced_duration = sum(duration for start, duration, channel in vad_reader.get_segments(activations))
    else:
        voiced_duration = numpy.sum(numpy.fromfile("%s/times.txt" % directory, sep="\n", dtype=numpy.int).reshape((-1, 2))[:,1])

    scaled_activations = vad_reader.scale_activations(activations)

    subs = pysrt.open("%s/nofluff.srt" % directory, "utf-8")
    text_segments = [sub.text for sub in subs]
    text_lengths, syllable_duration = syllables.text_lengths(text_segments, voiced_duration)

    alignment_info = moreno_recursion.AlignmentInfo(scaled_activations, text_segments, text_lengths, directory, syllable_duration, segment_seconds, window, min_len, use_fmllr, use_automaton, per_transcription_compile)
    alignment = alignment_info.get_alignment(passes=passes)

    write_srt((
        (text_segments[i], alignment[i] * 100, alignment[i] * 100 + text_lengths[i] * 100)
        for i in xrange(len(text_segments)) if i < len(alignment) and alignment[i] != -1
        ), "%s/generated.srt" % directory)

if __name__ == '__main__':
    main()
