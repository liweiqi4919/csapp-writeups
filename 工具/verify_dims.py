#!/usr/bin/env python3
# Verify a candidate width/height WITHOUT rendering the image:
# decompress the IDAT stream and check its length against h * (4w + 1).
import sys, struct, zlib

path = sys.argv[1] if len(sys.argv) > 1 else 'extracted/芙.png'
cands = [(int(sys.argv[2]), int(sys.argv[3]))] if len(sys.argv) > 3 else [(144, 1524), (2560, 1524)]

data = open(path, 'rb').read()
idat = b''
off = 8
while off + 8 <= len(data):
    ln = struct.unpack('>I', data[off:off + 4])[0]
    typ = data[off + 4:off + 8]
    if typ == b'IDAT':
        idat += data[off + 8:off + 8 + ln]
    off += 12 + ln
    if typ == b'IEND':
        break

raw = zlib.decompress(idat)
print("compressed IDAT bytes  :", len(idat))
print("decompressed raw bytes :", len(raw))
print()
for w, h in cands:
    want = h * (4 * w + 1)          # RGBA 8-bit: 4 bytes per pixel + 1 filter byte per row
    print("candidate %5d x %-5d -> expected raw = %-10d   %s"
          % (w, h, want, "MATCH" if want == len(raw) else "no match"))
