from lib import cd
from lib import time_helper
from lib import vad_reader
from lib import wavdump
from lib.subtitles import remove_fluff
import os
import argparse
import pysrt
import shlex
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(
        description="Prepare data for movie and store it in outdir"
    parser.add_argument('movie')
    parser.add_argument('outdir')
    parser.add_argument('-c', action='store_true')
    parser.add_argument('-v', action='store_true')
    parser.add_argument('-s', type=int, default=25)
    parser.add_argument('-t', type=float, default=0.0)
    args = parser.parse_args()
    movie = args.movie
    outdir = args.outdir
    use_channels = args.c
    use_vad_segments = args.v
    min_segment_length = args.s
    threshold = args.t
    prepare_data(movie, outdir, use_channels, use_vad_segments, min_segment_length, threshold)


def prepare_data(movie, outdir, use_channels, use_vad_segments, min_segment_length, threshold):
    directory = movie.rpartition('/')[0]
    shutil.rmtree(outdir, True)
    os.mkdir(outdir)

    wav_filename = '%s/audio.wav' % outdir
    wavdump.wavdump(movie, wav_filename)

    mono_filename = "%s/audio_mono.wav" % outdir
    command = "sox %s -e signed -b 16 %s remix -" % (wav_filename, mono_filename)
    print command
    subprocess.call(shlex.split(command))

    if (not use_channels) or use_vad_segments:
        delete_vad_output_segments()
        with cd.cd('VAD'):
            command = "./SMILExtract -C Standalone.conf -I ../%s" % mono_filename
            if not use_channels:
                command += " -csv ../%s/activations.csv" % outdir
            print command
            subprocess.call(shlex.split(command))


    os.mkdir("%s/segments" % outdir)
    if use_vad_segments:
        segments = os.listdir("VAD/output_segments")
        for segment in segments:
            command = "sox VAD/output_segments/%s %s/segments/%s" % (segment, outdir, segment)
            print command
            subprocess.call(command, shell=True)

    if use_channels:
        command = "soxi %s | grep Channels | awk '{print $3}'" % wav_filename
        channels = int(subprocess.check_output(command, shell=True))
        for channel in xrange(1, channels + 1):
            channel_filename = "%s/audio_%s.wav" % (outdir, channel)
            command = "sox %s -e signed -b 16 %s remix %s" % (wav_filename, channel_filename, channel)
            print command
            subprocess.call(shlex.split(command))

            csv_filename = '%s/activations_%s.csv' % (outdir, channel)
            with cd.cd('VAD'):
                command = "./SMILExtract -C Standalone.conf -I ../%s -csv ../%s" % (channel_filename, csv_filename)
                print command
                subprocess.call(shlex.split(command))

    activations = vad_reader.movie_activations(outdir)

    rate = int(subprocess.check_output("soxi %s/audio_mono.wav | grep 'Sample Rate' | awk '{print $4}'" % outdir, shell=True))
    if use_vad_segments:
        subprocess.call("./get_offsets.sh %s" % outdir, shell=True)
        with open("%s/durations.txt" % outdir) as durations:
            durations = map(lambda x: int(x) / (rate / 100), durations)
        with open("%s/offsets.txt" % outdir) as offsets:
            offsets = map(lambda x: int(x) / (rate / 50), offsets)
        os.remove("%s/durations.txt" % outdir)
        os.remove("%s/offsets.txt" % outdir)
        if use_channels:
            segments = zip(offsets, durations)
            channels = vad_reader.voiciest_channel_segments(segments, activations)
            segments = [(offset / 10, duration / 10, channel) for (offset, duration), channel in zip(segments, channels)]
        else:
            segments = [(offset / 10, duration / 10) for offset, duration in zip(offsets, durations)]
    else:
        segments = vad_reader.get_segments(activations, min_segment_length, threshold)

    with open("%s/times.txt" % outdir, 'w') as times:
        times.write("".join("%s %s\n" % (segment[0], segment[1]) for segment in segments))

    if use_channels or not use_vad_segments:
        for segment in os.listdir("%s/segments" % outdir):
            os.remove("%s/segments/%s" % (outdir, segment))
        generate_segments(outdir, segments, use_channels)

    generate_features(outdir, rate)

    no_fluff_srt = '%s/nofluff.srt' % outdir
    remove_fluff.remove_fluff("%s/subs.srt" % directory, no_fluff_srt)

    with open("%s/transcription.txt" % outdir, 'w') as transcription:
        transcription.write(" ".join(' '.join(remove_fluff.corpusize(sub.text) for sub in pysrt.open("%s/nofluff.srt" % outdir)).split()).encode('utf-8'))
    subprocess.call("echo ' (uwotm8)' >> %s/transcription.txt" % outdir, shell=True)

    delete_vad_output_segments()


def generate_segments(outdir, segments, use_channels):
    command = "ffmpeg -y -i %s/audio_{}.wav -acodec copy -ss {} -t {} %s/segments/seg_{}.wav" % (outdir, outdir)
    for i, (start, duration, channel) in enumerate(segments):
        start_string = time_helper.time_from_millis(start * 100).strftime("%H:%M:%S.%f")[:-3]
        duration_string = time_helper.time_from_millis(duration * 100).strftime("%H:%M:%S.%f")[:-3]
        seg_10_digits = "0" * (10 - len(str(i + 1))) + str(i + 1)
        channel_string = (channel + 1) if use_channels else "mono"
        curr_command = command.format(channel_string, start_string, duration_string, seg_10_digits)
        print curr_command
        subprocess.call(shlex.split(curr_command))


def generate_features(outdir, rate):
    with open("%s/segments.scp" % outdir, 'w') as scp:
        segment_files = sorted(os.listdir("%s/segments" % outdir))
        scp.write("".join("%s %s/segments/%s\n" % (i + 1, outdir, name) for i, name in enumerate(segment_files)))
    command = "./mfcc.sh %s %s" % (outdir, rate)
    print command
    subprocess.call(shlex.split(command))


def delete_vad_output_segments():
    for segment in os.listdir("VAD/output_segments"):
        os.remove("VAD/output_segments/%s" % segment)

if __name__ == '__main__':
    main()
