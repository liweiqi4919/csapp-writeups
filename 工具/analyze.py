import zlib, binascii, struct, sys

INNER = "/mnt/d/DSH/csapp/ctf-writeups/QuestionCTF2026/extracted/frist/final.zip"
TXT   = "/mnt/d/DSH/csapp/ctf-writeups/QuestionCTF2026/extracted/frist/Is_this_a_real_flag.txt"

b = open(INNER, 'rb').read()
print("final.zip size =", len(b))
print()

data = None
crc_local = None
time_local = None

off = 0
while True:
    i = b.find(b'PK\x03\x04', off)
    if i < 0:
        break
    ver, flag, meth, mt, md, crc, csz, usz, fnl, efl = struct.unpack_from('<HHHHHIIIHH', b, i + 4)
    name = b[i + 30:i + 30 + fnl].decode('latin1')
    print("LOCAL @0x%04X name=%-16r flag=0x%04X meth=%d crc=0x%08X csz=%d usz=%d efl=%d time=0x%04X date=0x%04X"
          % (i, name, flag, meth, crc, csz, usz, efl, mt, md))
    if name == 'flag/flag.txt':
        d = i + 30 + fnl + efl
        data = b[d:d + csz]
        crc_local = crc
        time_local = mt
        print("  data offset = 0x%04X, len = %d" % (d, len(data)))
        print("  data hex    =", binascii.hexlify(data).decode())
        print("  data[0:12]  =", binascii.hexlify(data[0:12]).decode(), "(ZipCrypto header?)")
        print("  data[12:]   =", binascii.hexlify(data[12:]).decode(), "(payload, %d bytes)" % (len(data) - 12))
        print("  data[11] = 0x%02X   crc>>24 = 0x%02X   time>>8 = 0x%02X"
              % (data[11], (crc >> 24) & 0xff, (mt >> 8) & 0xff))
    off = i + 4

if data is None:
    print("flag/flag.txt not found")
    sys.exit(1)

print()
print("=== zipcrypto check byte test ===")
print("  byte#11 of data      = 0x%02X" % data[11])
print("  high byte of CRC     = 0x%02X" % ((crc_local >> 24) & 0xff))
print("  high byte of dosTime = 0x%02X" % ((time_local >> 8) & 0xff))
print("  matches CRC?   ", data[11] == ((crc_local >> 24) & 0xff))
print("  matches time?  ", data[11] == ((time_local >> 8) & 0xff))

print()
print("=== try raw deflate from every offset ===")
hit = False
for o in range(len(data)):
    try:
        dz = zlib.decompressobj(-15)
        r = dz.decompress(data[o:])
        if dz.eof and r:
            printable = all(32 <= c < 127 or c in (9, 10, 13) for c in r)
            print("  offset %2d -> %d bytes, eof=%s, printable=%s : %r" % (o, len(r), dz.eof, printable, r[:70]))
            hit = True
    except Exception:
        pass
if not hit:
    print("  none - no valid raw deflate stream at any offset")

print()
print("=== single-byte XOR scan for 'CTF{' ===")
found = False
for span, label in ((data, "whole 35"), (data[12:], "payload 23")):
    for k in range(256):
        x = bytes(c ^ k for c in span)
        if b'CTF{' in x or b'ctf{' in x:
            print("  %s xor 0x%02X -> %r" % (label, k, x[:70]))
            found = True
if not found:
    print("  no single-byte XOR produces 'CTF{'")

print()
print("=== printable check of payload (data[12:]) ===")
print("  bytes:", binascii.hexlify(data[12:]).decode())
print("  ascii:", ''.join(chr(c) if 32 <= c < 127 else '.' for c in data[12:]))

print()
print("=== decoy txt raw bytes ===")
t = open(TXT, 'rb').read()
print("  size =", len(t))
print("  hex  =", binascii.hexlify(t).decode())
print()
for line in t.split(b'\n'):
    if b'qctf' in line.lower():
        print("  qctf line repr :", repr(line))
        print("  qctf line hex  :", binascii.hexlify(line).decode())
