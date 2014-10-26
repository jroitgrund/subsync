import csv
import glob
import numpy
import BitVector


def get_segments(activations_list, min_duration, threshold):
    activations = numpy.mean(activations_list, axis=0)
    sounds = BitVector.BitVector(size=activations.shape[0])
    for i, activation in enumerate(activations):
        sounds[i] = activation > threshold

    segments = []
    current_segment_duration = 0
    current_segment_start = 0
    start = 0
    for group in sounds.runs():
        voice = group[0] == '1'
        duration = len(group)

        extending_segment = current_segment_duration > 0
        known_sound = duration >= min_duration

        if not extending_segment:
            if known_sound and voice:
                current_segment_start = start
                current_segment_duration = duration

        if extending_segment:
            if known_sound and not voice:
                segments.append((current_segment_start, current_segment_duration))
                current_segment_duration = 0
            else:
                current_segment_duration += duration

        start += duration

    if current_segment_duration > 0:
        segments.append((current_segment_start, current_segment_duration))

    return [(start / 10, duration / 10, most_voicy_channel(start, duration, activations_list)) for start, duration in segments]


def scale_activations(mult_activations):
    activations = numpy.multiply(numpy.max(mult_activations, axis=0), 10000000000)
    activations = numpy.rint(activations).astype(int)
    scaled_activations = numpy.zeros(activations.shape[0] / 10 + (0 if activations.shape[0] % 10 == 0 else 1), dtype=numpy.int)
    for i, start in enumerate(xrange(0, activations.shape[0], 10)):
        scaled_activations[i] = activations[start:start+10].sum()
    return scaled_activations


def activations_from_csv(infiles):
    data_point_count = sum(1 for line in open(infiles[0]))
    activations = numpy.zeros((len(infiles), data_point_count), dtype=numpy.float)
    for i, infile in enumerate(infiles):
        with open(infile) as csv_output:
            reader = csv.reader(csv_output)
            for j, line in enumerate(reader):
                activations[i, j] = float(line[1])
    return activations


def movie_activations(directory):
    csv_files = glob.glob("%s/activations*.csv" % directory)
    return activations_from_csv(csv_files)


def most_voicy_channel(start, duration, activations):
    sums = [numpy.sum(activations[i][start:start+duration]) for i in xrange(activations.shape[0])]
    return sums.index(max(sums))


def voiciest_channel_segments(segments, activations):
    return [most_voicy_channel(start, duration, activations)
            for start, duration in segments]
