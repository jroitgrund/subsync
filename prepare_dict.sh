#!/bin/bash
echo $@
set -x
locdata=$1/local
locdict=$locdata/dict

gawk 'NR==FNR{words[$1]; next;} !($1 in words)' \
  data/cmudict-plain.txt $locdata/vocab-full.txt |\
  egrep -v '<.?s>' > $locdict/vocab-oov.txt

gawk 'NR==FNR{words[$1]; next;} ($1 in words)' \
  $locdata/vocab-full.txt data/cmudict-plain.txt |\
  egrep -v '<.?s>' > $locdict/lexicon-iv.txt

wc -l $locdict/vocab-oov.txt
wc -l $locdict/lexicon-iv.txt

export PYTHONPATH=/home/jroitgrund/src/kaldi-stable/egs/voxforge/s5/tools/g2p/lib/python2.7/site-packages
python /home/jroitgrund/src/kaldi-stable/egs/voxforge/s5/tools/g2p/g2p.py \
  --model=data/g2p_model --apply $locdict/vocab-oov.txt > $locdict/lexicon-oov.txt

cat $locdict/lexicon-oov.txt $locdict/lexicon-iv.txt |\
  sort > $locdict/lexicon.txt

cp data/{silence_phones,optional_silence,nonsilence_phones}.txt $locdict

echo -e "!SIL\tSIL" >> $locdict/lexicon.txt

# Some downstream scripts expect this file exists, even if empty
touch $locdict/extra_questions.txt
