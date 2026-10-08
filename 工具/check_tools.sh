#!/bin/bash
echo "=== WSL tools ==="
for t in unzip zipinfo 7z 7za 7zr fcrackzip john hashcat bkcrack python3 xxd; do
  p=$(command -v "$t" 2>/dev/null)
  if [ -n "$p" ]; then
    echo "  [have] $t -> $p"
  else
    echo "  [none] $t"
  fi
done

echo ""
echo "=== final.zip 在 7-Zip/unzip 眼里是什么样 ==="
Z="/mnt/d/DSH/csapp/ctf-writeups/QuestionCTF2026/extracted/frist/final.zip"
if [ -f "$Z" ]; then
  unzip -v "$Z" 2>&1 | head -20
else
  echo "  final.zip not found at $Z"
fi

echo ""
echo "=== 外层 frist.zip 呢 ==="
Z2="/mnt/d/DSH/csapp/ctf-writeups/frist.zip"
if [ -f "$Z2" ]; then
  unzip -v "$Z2" 2>&1 | head -20
fi
