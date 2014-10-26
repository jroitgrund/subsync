from lib import time_helper

_TIME_FORMAT = "%H:%M:%S,%f"


def write_srt(subs, outfile):
    with open(outfile, 'w') as subfile:
        for i, (text, start, end) in enumerate(subs):
            start_time = time_helper.time_from_millis(start)
            end_time = time_helper.time_from_millis(end)
            subfile.write("%s\n" % (i + 1))
            subfile.write(
                "%s --> %s\n" % (start_time.strftime(_TIME_FORMAT)[:-3],
                                 end_time.strftime(_TIME_FORMAT)[:-3]))
            subfile.write(text.encode('utf-8'))
            subfile.write("\n\n")
