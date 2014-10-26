#!/bin/bash
echo $@
set -x
locdata=$1/local
loctmp=$locdata/tmp

ngram-count -lm $locdata/lm.arpa -wbdiscount -text $1/corpus.txt -order 3 -write-vocab $locdata/vocab-full.txt
