import pysrt
import re
import string


def corpusize(sub):
    return re.sub(r"(^ *| *$)", "", re.sub("\n+", "\n", re.sub(" +", " ", re.sub(r"(,|;|:|-)", " ",
                  re.sub(r"(\?|!|\.)", "\n", sub + "\n")))), flags=re.MULTILINE).upper()


def rmf(line):
    line = re.sub(r"(^ *-)", "", re.sub(r"([a-zA-Z]+:)|(\[.*\])|(\<[^\<]*\>)|" + '"',
                  "", line), flags=re.MULTILINE)
    line = string.join(line.split())
    return line


def remove_fluff(infile, outfile):
    subs = pysrt.open(infile)
    for sub in subs:
        sub.text = rmf(sub.text)
    subs.save(outfile, 'utf-8')
