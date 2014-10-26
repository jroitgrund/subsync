import numpy
import itertools
import re
from lib.syllables import SyllableCounter
from lib.subtitles import remove_fluff
import os
from os import path
import pysrt
import string
import shutil
import subprocess
import sys


def get_anchors(directory, duration_seconds, alignment, texts, syllable_duration, segment_seconds, window, min_len, use_fmllr, use_automaton, per_transcription_compile):
    working = "%s/data" % directory
    shutil.rmtree(working, True)
    os.mkdir(working)
    false_positives = 0
    results = []
    for minute in xrange(duration_seconds / segment_seconds):
        times = numpy.array([time for sub, time in alignment], numpy.int)
        first, last = times_in_minute(minute, times, segment_seconds, window)
        minute_texts = texts[first:last]
        times = numpy.fromfile("%s/times.txt" % directory, sep="\n", dtype=numpy.int).reshape((-1, 2))[:,0]
        first, last = times_in_minute(minute, times, segment_seconds)
        prepare_data(directory, minute_texts, first, last, use_fmllr, use_automaton)
        if per_transcription_compile:
            res, false_pos = compile_results(directory, min_len, numpy.fromfile("%s/times.txt" % directory, sep="\n", dtype=numpy.int).reshape((-1, 2)), True)
            results.extend(res)
            false_positives += false_pos
            try:
                os.remove("%s/transcriptions.txt" % working)
                os.remove("%s/alignments.txt" % working)
            except:
                pass

    if not per_transcription_compile:
        results, false_positives = compile_results(directory, min_len, numpy.fromfile("%s/times.txt" % directory, sep="\n", dtype=numpy.int).reshape((-1, 2)), per_transcription_compile)
    print "Total count: have %s anchors, probably %s false positives" % (len(results), false_positives)
    syllable_counter = SyllableCounter()
    results = [find_alignment(expression, times[segment - 1], segment_offset, texts, syllable_counter, syllable_duration) for expression, segment, segment_offset in results]
    seen = {}
    unduped = []
    for sub_num, time in results:
        if sub_num in seen:
            continue
        seen[sub_num] = 1
        unduped.append((sub_num, time))
    print "\n".join("%s is at %s" % result for result in unduped)
    return unduped


def find_alignment(expression, segment_time, segment_offset, texts, syllable_counter, syllable_duration):
    try:
        sub_num, sub = next((i, text) for i, text in enumerate(texts) if expression in text)
    except:
        sub_num, sub = next((num, text) for num, text in [(i, ' '.join(itertools.imap(lambda x: ' '.join(x.split()), texts[i:])))
                for i in xrange(len(texts) - 1, -1, -1)] if expression in text)
    before = sub[:string.find(sub, expression)]
    before_time = sum(syllable_counter.count_syllables(word) for word in before.split()) * syllable_duration
    print "%s is before, and lasts %s deciseconds" % (before, before_time)
    return (sub_num, int(segment_time + segment_offset - before_time))


def prepare_data(directory, texts, first, last, use_fmllr, use_automaton):
    working = "%s/data" % directory
    with open("%s/corpus.txt" % working, 'w') as corpus:
        corpus.write("".join(texts))
    with open("%s/curr_transcription.txt" % working, 'w') as curr_transcription:
        curr_transcription.write(" ".join("".join(texts).split()))
    subprocess.call("echo ' (uwotm8)' >> %s/curr_transcription.txt" % working, shell=True)

    for feat_suffix in ["", "_3b", "_3b_mmi"]:
        command = "sed -n %s,%sp %s/feats%s.scp > %s/curr%s.scp" % (first + 1, last, directory, feat_suffix, working, feat_suffix)
        print command
        subprocess.call(command, shell=True)
    command = "./run_asr.sh%s%s %s" % (" -f" if use_fmllr else "", " -a" if use_automaton else "", working)
    print command
    subprocess.call(command, shell=True)


def times_in_minute(minute, times, segment_seconds, extra=0):
    start = (minute - extra) * segment_seconds * 10
    end = (minute + extra + 1) * segment_seconds * 10
    sub_indexes = numpy.searchsorted(times, [start, end])
    return sub_indexes[0], sub_indexes[1]


def compile_results(directory, min_len, times, per_transcription_compile):
    working = "%s/data" % directory
    if not path.isfile("%s/transcriptions.txt" % working):
        return [], 0
    correct_trans = "%s/curr_transcription.txt" % working if per_transcription_compile else "%s/transcription.txt" % directory
    subprocess.call("awk '{$1=\"\";printf(\"%%s \", $0)}' %s/transcriptions.txt > %s/hyp.txt" % (working, working), shell=True)
    subprocess.call("echo ' (uwotm8)' >> %s/hyp.txt" % working, shell=True)
    subprocess.call("sclite -r %s -h %s/hyp.txt -i rm -o stdout sgml | sed -n 4p > %s/align.sgml" % (correct_trans, working, working), shell=True)
    with open('%s/align.sgml' % working) as sgml:
        alignments = ''.join(line for line in sgml).split(":")
    pairs = [(part[0], part[2]) for part in map(lambda x: x.partition(','), alignments)]
    groups = [list(group) for alignment, group in itertools.groupby(pairs, lambda x: x[0]) if alignment == 'C']
    groups = filter(lambda x: len(x) >= min_len, groups)
    expressions = [map(lambda x: x[1].partition('"')[2].partition('"')[0], pair) for pair in groups]
    expressions = [" ".join(expression).upper() for expression in expressions]

    with open("%s/transcriptions.txt" % working) as transcriptions:
        transcriptions = [(int(segment), ' '.join(transcription.split())) for segment, _, transcription in (tuple(t.partition(' ')) for t in transcriptions)]

    segment = 0
    false_positives = 0
    pairs = []
    print expressions
    for expression in expressions:
        try:
            segment = next(index for index, transcription in transcriptions if expression in transcription)
        except:
            try:
                segment = next(index for index, transcription in [(transcriptions[i][0], ' '.join(' '.join(map(lambda x: x[1], transcriptions[i:])).split()))
                    for i in xrange(len(transcriptions) - 1, -1, -1)] if expression in transcription)
            except:
                print "Can't find expression %s in transcriptions %s" % (expression, transcriptions)
                sys.exit(-1)
        print "%s is correct in segment %s" % (expression, segment)
        segment_start = times[segment - 1][0] * 100
        segment_end = times[segment - 1][1] * 100 + segment_start
        try:
            sub = next(remove_fluff.corpusize(sub.text) for sub in pysrt.open("%s/nofluff.srt" % directory) if sub.end.ordinal > segment_start and sub.start.ordinal < segment_end)
            if expression not in sub and sub not in expression:
                print "%s is probably a false positive: not in %s" % (expression, sub)
                false_positives += 1
        except:
            print "Couldn't find a sub for segment between %s and %s miliseconds" % (segment_start, segment_end)
        pairs.append((expression, segment))
    print "Have %s anchors, probably %s false positives" % (len(expressions), false_positives)

    with open("%s/alignments.txt" % working) as alignments:
        alignments = "".join(list(alignments))

    results = []

    for expression, segment in pairs:
        rg = "\\s*".join(r"[0-9]* [0-9]* ([0-9]*\.[0-9]*) [0-9]*\.[0-9]* %s" % word for word in expression.split()[:99])
        try:
            in_segment = float(re.search(rg, alignments).group(1)) * 10
        except:
            print "Can't find expression %s using regex %s in alignments: %s" % (expression, rg, alignments)
            sys.exit(-1)
        result = (expression, segment, in_segment)
        results.append(result)

    return results, false_positives
