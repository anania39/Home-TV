#!/usr/bin/env bash
set -euo pipefail
SSH="ssh -i ~/.ssh/id_ed25519_oci -o ConnectTimeout=20 ubuntu@92.5.71.162"
REMOTEDIR=/home/ubuntu/tvhub-v8.0.7-stage/scripts
B64="$REMOTEDIR/_v807_pristine.b64"

# clear any previous b64
$SSH bash -lc "rm -f '$B64'"
echo "cleared remote b64"

count=0
for f in _chunk_*; do
  cat "$f" | $SSH bash -lc "cat >> '$B64'" || { echo "FAIL stream $f"; exit 1; }
  count=$((count+1))
  printf .
done
echo
echo "streamed $count chunks"

# verify remote b64
$SSH bash -lc "echo b64_size; wc -c '$B64'; echo b64_head; head -c 60 '$B64'; echo; echo b64_tail; tail -c 60 '$B64'"
