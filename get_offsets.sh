#!/bin/bash
echo $@
set -x

main_offset=$(python lib/searchbin.py -m 1 -t data $1/audio_mono.wav | grep Match | awk '{print $4}')
main_offset=$((main_offset + 4))

for segment in $1/segments/*
do
  search=${offset:-0}
  curr_offset=$(python lib/searchbin.py -m 1 -t data $segment | grep Match | awk '{print $4}')
  curr_offset=$((curr_offset + 4))
  dd if=$segment skip=$curr_offset of=$1/segment_temp >& /dev/null
  offset=$(python lib/searchbin.py -m 1 -s $search -f $1/segment_temp $1/audio_mono.wav | grep Match | awk '{print $4}')
  search=$offset
  offset=$((offset - $main_offset))
  echo $offset >> $1/offsets.txt

  echo "$(soxi $segment | grep Duration | awk '{print $5}')" >> $1/durations.txt
done

rm $1/segment_temp