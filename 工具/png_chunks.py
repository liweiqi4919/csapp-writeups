#!/usr/bin/env python3
# Walk PNG chunks, print each one, verify CRC of every chunk.
# Usage: python3 png_chunks.py <file.png>
import sys, struct, zlib

if len(sys.argv) < 2:
    print("Usage: python3 png_chunks.py <file.png>")
    sys.exit(1)

path = sys.argv[1]
data = open(path, 'rb').read()

print("=" * 72)
print(" file      :", path)
print(" file size :", len(data), "bytes")
print(" PNG magic :", "OK" if data[:8] == b'\x89PNG\r\n\x1a\n' else "**NOT A PNG**")
print("=" * 72)

off = 8
n = 0
bad = []
while off + 8 <= len(data):
    ln = struct.unpack('>I', data[off:off + 4])[0]
    typ = data[off + 4:off + 8]
    try:
        t = typ.decode('ascii')
    except Exception:
        t = str(typ)
    body = data[off + 8:off + 8 + ln]
    end = off + 12 + ln
    if end > len(data):
        print(f"#{n:02d} off=0x{off:06X} len={ln} type={t}  -> RUNS PAST END OF FILE")
        break
    crc_stored = struct.unpack('>I', data[off + 8 + ln:end])[0]
    crc_calc = zlib.crc32(typ + body) & 0xffffffff
    ok = (crc_stored == crc_calc)
    if not ok:
        bad.append((n, t, off, crc_stored, crc_calc))
    flag = "OK" if ok else "** CRC MISMATCH **"
    print(f"#{n:02d} off=0x{off:06X}  len={ln:<8} type={t:<6} stored=0x{crc_stored:08X} calc=0x{crc_calc:08X}  {flag}")
    if t == 'IHDR':
        w, h = struct.unpack('>II', body[:8])
        print(f"        IHDR -> width={w}  height={h}  bitdepth={body[8]}  colortype={body[9]}"
              f"  comp={body[10]}  filter={body[11]}  interlace={body[12]}")
        print(f"        width  bytes on disk: {' '.join('%02X' % b for b in body[0:4])}"
              f"   (0x{w:08X})")
        print(f"        height bytes on disk: {' '.join('%02X' % b for b in body[4:8])}"
              f"   (0x{h:08X})")
    if t == 'IEND':
        print("        (IEND - end of PNG)")
        break
    off = end
    n += 1
    if n > 200:
        print("... stopped after 200 chunks")
        break

print("=" * 72)
if bad:
    print(" chunks with WRONG crc:", len(bad))
    for n_, t, o, s, c in bad:
        print(f"   #{n_:02d} {t} at offset 0x{o:06X}   stored=0x{s:08X}  real=0x{c:08X}")
else:
    print(" all chunk CRCs are correct")
print("=" * 72)
