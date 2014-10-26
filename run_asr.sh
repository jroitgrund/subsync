echo $@
set -x
export train_cmd=run.pl
export decode_cmd=run.pl

. ./path.sh

no_fmllr=true

while :
do
  case $1 in
    -a)
      automaton=true
      shift
      ;;
    -f)
      no_fmllr=false
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      printf >&2 'WARN: Unknown option (ignored): %s\n' "$1"
      shift
      ;;
    *)
      break
      ;;
esac
done

data=$1

njobs=2
mkdir -p $data/local/dict
prepare_lm.sh $data
prepare_dict.sh $data
utils/prepare_lang.sh $data/local/dict '!SIL' $data/local/lang $data/lang || exit 1

mkdir -p $data/local/lm_tmp
cat $data/local/lm.arpa | \
   utils/find_arpa_oovs.pl $data/lang/words.txt > $data/local/lm_tmp/oovs.txt

if [ "$automaton" = true ]; then
  python lib/factor_automaton.py -f $data/corpus.txt > $data/text_g_fst
else
  cat $data/local/lm.arpa | \
    grep -v '<s> <s>' | \
    grep -v '</s> <s>' | \
    grep -v '</s> </s>' | \
    arpa2fst - | fstprint > $data/text_g_fst
fi

cat  $data/text_g_fst | \
  utils/remove_oovs.pl $data/local/lm_tmp/oovs.txt | \
  utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=$data/lang/words.txt \
    --osymbols=$data/lang/words.txt  --keep_isymbols=false --keep_osymbols=false | \
  fstrmepsilon > $data/lang/G.fst
fstisstochastic $data/lang/G.fst

if [ "$no_fmllr" = true ]; then
  echo "tri2b pass"
  utils/mkgraph.sh $data/lang data/tri2b $data/decode_graph || exit 1
  gmm-decode-faster --word-symbol-table=$data/decode_graph/words.txt --allow-partial=true data/tri2b/final_decode.mdl $data/decode_graph/HCLG.fst scp:$data/curr.scp "ark,t:$data/transcription.txt" "ark:/dev/null" "ark:$data/lattice.ark"
  lattice-align-words $data/lang/phones/word_boundary.int data/tri2b/final.mdl ark:$data/lattice.ark ark:$data/words.ark
else
  echo "tri3b pass"
  utils/mkgraph.sh $data/lang data/tri3b $data/decode_graph || exit 1

  #speaker independent decoding
  gmm-latgen-faster --acoustic-scale=0.083333 --max-active=2000 --beam=10.0 --lattice-beam=6.0 --allow-partial=true \
  data/tri3b/final.alimdl \
  $data/decode_graph/HCLG.fst \
  scp:$data/curr_3b_mmi.scp "ark:|gzip -c > $data/lat.gz" 

  silphonelist=`cat $data/decode_graph/phones/silence.csl`

  #first pass fMLLR transforms
  gunzip -c $data/lat.gz | lattice-to-post --acoustic-scale=0.083333 ark:- ark:- | \
  weight-silence-post 0.01 "$silphonelist" data/tri3b/final.alimdl ark:- ark:- | \
  gmm-post-to-gpost data/tri3b/final.alimdl scp:$data/curr_3b.scp ark:- ark:- | \
  gmm-est-fmllr-gpost --fmllr-update-type=full data/tri3b/final.mdl scp:$data/curr_3b.scp ark,s,cs:- ark:$data/pre_trans

  #main lattice generation pass
  gmm-latgen-faster --acoustic-scale=0.083333 --max-active=7000 --beam=13.0 --lattice-beam=6.0 --allow-partial=true \
  data/tri3b/final.alimdl \
  $data/decode_graph/HCLG.fst scp:$data/curr_3b_mmi.scp "ark:|gzip -c > $data/lat_tmp.gz"

  #second pass fMLLR transform
  lattice-determinize-pruned --acoustic-scale=0.083333 "ark:gunzip -c $data/lat_tmp.gz|" ark:- | \
  lattice-to-post --acoustic-scale=0.083333 ark:- ark:- | \
  weight-silence-post 0.01 "$silphonelist" data/tri3b/final.mdl ark:- ark:- | \
  gmm-est-fmllr --fmllr-update-type=full data/tri3b/final.mdl "ark:transform-feats ark:$data/pre_trans scp:$data/curr_3b_mmi.scp ark:- |" \
  ark,s,cs:- ark:$data/trans_tmp && \
  compose-transforms --b-is-affine=true ark:$data/trans_tmp ark:$data/pre_trans ark:$data/trans

  #final pass of acoustic rescoring
  gmm-rescore-lattice data/tri3b_mmi/final.mdl "ark:gunzip -c $data/lat_tmp.gz|" "ark:transform-feats ark:$data/trans scp:$data/curr_3b_mmi.scp ark:- |" ark:- | \
  lattice-determinize-pruned --acoustic-scale=0.083333 ark:- "ark:|gzip -c > $data/lat.gz" && rm $data/lat_tmp.gz

  #text
  lattice-best-path --word-symbol-table=$data/decode_graph/words.txt "ark:gunzip -c $data/lat.gz|" "ark,t:$data/transcription.txt"
  lattice-1best "ark:gunzip -c $data/lat.gz|" ark:$data/lattice.ark
  lattice-align-words $data/lang/phones/word_boundary.int data/tri3b/final.mdl ark:$data/lattice.ark ark:$data/words.ark
fi
int2sym.pl -f 2- $data/decode_graph/words.txt <$data/transcription.txt >>$data/transcriptions.txt
nbest-to-ctm ark:$data/words.ark - | \
utils/int2sym.pl -f 5 $data/lang/words.txt >> $data/alignments.txt

