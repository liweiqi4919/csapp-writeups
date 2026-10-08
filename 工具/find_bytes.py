#!/usr/bin/env python3
# Find every occurrence of a byte pattern in a file and show context.
# Usage: python3 find_bytes.py <file> <text> [--hex HEXBYTES]
import sys

path = sys.argv[1]
arg = sys.argv[2]

if arg.startswith('--hex'):
    needle = bytes.fromhex(arg.split('=', 1)[1] if '=' in arg else sys.argv[3])
else:
    needle = arg.encode()

data = open(path, 'rb').read()
print("file   :", path, "(%d bytes)" % len(data))
print("needle :", needle, "(%d bytes)" % len(needle))
print("-" * 70)

i = 0
n = 0
while n < 30:
    j = data.find(needle, i)
    if j < 0:
        break
    lo = max(0, j - 20)
    hi = min(len(data), j + len(needle) + 20)
    ctx = data[lo:hi]
    shown = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
    print("0x%08X  %s" % (j, shown))
    i = j + 1
    n += 1

print("-" * 70)
print("occurrences:", n, "" if n < 30 else "(capped at 30)")
