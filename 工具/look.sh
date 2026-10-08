#!/bin/bash
# CTF attachment triage - the "four steps" from _第一次CTF怎么下手.md
# Usage: bash look.sh <file>

f="$1"
if [ -z "$f" ]; then
  echo "Usage: bash look.sh <file>"
  exit 1
fi
if [ ! -f "$f" ]; then
  echo "Not found: $f"
  exit 1
fi

echo "=============================================="
echo " FILE: $f"
echo "=============================================="
echo
echo "--- size ---"
printf "  %s bytes\n" "$(stat -c %s "$f")"
echo
echo "--- sha256 ---"
sha256sum "$f" | awk '{print "  " $1}'
echo
echo "--- 1. file  (what is this really?) ---"
file "$f"
echo
echo "--- 2. strings, first 30 lines ---"
strings "$f" | head -30
echo
echo "--- 3. hex head, first 16 lines  (is the magic right?) ---"
xxd "$f" | head -16
echo
echo "--- 4. hex tail, last 8 lines  (trailing data?) ---"
xxd "$f" | tail -8
echo
echo "--- 5. grep for flag-ish words ---"
strings "$f" | grep -i -E 'flag|ctf|key|pass|secret|hint' | head -20
if [ $? -ne 0 ]; then echo "  (none found)"; fi
echo
echo "--- 6. interesting magic bytes anywhere? ---"
strings -t x "$f" 2>/dev/null | grep -i -E 'PK|JFIF|PNG|GIF|ID3|RIFF|OggS|MZ|ELF' | head -10
if [ $? -ne 0 ]; then echo "  (none found)"; fi
echo
echo "=============================================="
