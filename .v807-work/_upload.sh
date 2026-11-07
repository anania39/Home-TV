#!/usr/bin/env bash
set -euo pipefail
SSH="ssh -i ~/.ssh/id_ed25519_oci -o ConnectTimeout=20 ubuntu@92.5.71.162"
RB64=/home/ubuntu/tvhub-v8.0.7-stage/scripts/_v807_pristine.b64
$SSH rm -f "$RB64"
FAIL=0
for f in _chunk_*; do
  b64=$(base64 -w0 < "$f")
  if ! $SSH bash -c "printf '%s' '$b64' >> '$RB64'"; then
    echo "FAIL $f"
    FAIL=1
    break
  fi
  printf .
done
echo
echo "upload rc=$FAIL"
$SSH bash -c 'echo b64_size; wc -c /home/ubuntu/tvhub-v8.0.7-stage/scripts/_v807_pristine.b64; echo b64_head; head -c 60 /home/ubuntu/tvhub-v8.0.7-stage/scripts/_v807_pristine.b64; echo; echo b64_tail; tail -c 60 /home/ubuntu/tvhub-v8.0.7-stage/scripts/_v807_pristine.b64'
