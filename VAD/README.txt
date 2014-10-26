To run the vad on a wave file:

  sox my.wav -c 1 -s -2 input.wav
  ./SMILExtract -C Standalone.conf -I input.wav -csv vad.csv

In output_segments/*.wav the voice segments will be stored
In vad.csv the raw vad activations (-1 to +1) will be dumped. First column is a timestamp in seconds, second column (after the ,) is the vad activation.


