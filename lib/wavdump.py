import subprocess


def wavdump(infile, outfile):
    command = "mplayer -ao pcm:file=%s,fast -vc null -vo null %s" \
        % (outfile, infile)
    print command
    return subprocess.call(command, shell=True)
