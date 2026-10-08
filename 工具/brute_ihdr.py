#!/usr/bin/env python3
# PNG IHDR CRC brute-forcer.
#
# The IHDR chunk's CRC32 was wiped to 00000000, and the challenge text gives us
# the original value: 051F503E.  CRC32 is a fingerprint of the IHDR *content*:
#
#     CRC32( b"IHDR" + width(4) + height(4) + bitdepth/colortype/... )
#
# Width and height are small integers, so we just try every pair until the
# computed fingerprint equals the target.
#
# Usage: python3 brute_ihdr.py [WMAX] [HMAX]
import sys, zlib, struct, time

TARGET = 0x051F503E
SUFFIX = bytes([8, 6, 0, 0, 0])   # bitdepth=8 colortype=6(RGBA) comp=0 filter=0 interlace=0

WMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
HMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 2000

print("target CRC = 0x%08X" % TARGET)
print("searching width 1..%d  x  height 1..%d   (%d combos)" % (WMAX, HMAX, WMAX * HMAX))
t0 = time.time()

hits = []
for w in range(1, WMAX + 1):
    c1 = zlib.crc32(b'IHDR' + struct.pack('>I', w))
    for h in range(1, HMAX + 1):
        if zlib.crc32(struct.pack('>I', h) + SUFFIX, c1) & 0xffffffff == TARGET:
            hits.append((w, h))
            raw = h * (4 * w + 1)
            print("  ** FOUND **  width=%d  height=%d   raw pixel data = %d bytes" % (w, h, raw),
                  flush=True)

dt = time.time() - t0
print("done in %.1f s   hits = %d" % (dt, len(hits)))
if not hits:
    print("nothing found - widen the range, e.g.  python3 brute_ihdr.py 5000 5000")
