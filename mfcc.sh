#!/bin/bash

echo $@
set -x
. ./path.sh

compute-mfcc-feats --sample-frequency=$2 --use-energy=false scp:${1}/segments.scp ark:${1}/mfcc.ark
compute-cmvn-stats ark:${1}/mfcc.ark ark:${1}/cmvn.ark

apply-cmvn --norm-vars=false ark:${1}/cmvn.ark ark:${1}/mfcc.ark ark:- | \
splice-feats ark:- ark:- | \
transform-feats data/tri2b/final.mat ark:- ark,scp:${1}/feats.ark,${1}/feats.scp

apply-cmvn --norm-vars=false ark:${1}/cmvn.ark ark:${1}/mfcc.ark ark:- | \
splice-feats ark:- ark:- | \
transform-feats data/tri3b/final.mat ark:- ark,scp:${1}/feats.ark,${1}/feats_3b.scp

apply-cmvn --norm-vars=false ark:${1}/cmvn.ark ark:${1}/mfcc.ark ark:- | \
splice-feats ark:- ark:- | \
transform-feats data/tri3b_mmi/final.mat ark:- ark,scp:${1}/feats.ark,${1}/feats_3b_mmi.scp

rm $1/cmvn.ark $1/mfcc.ark
