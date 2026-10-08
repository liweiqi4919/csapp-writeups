import struct, binascii, itertools, zlib, sys, time

def make_crc_table():
    tbl = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if (c & 1) else (c >> 1)
        tbl.append(c & 0xFFFFFFFF)
    return tbl

CRCT = make_crc_table()

class ZipCrypto:
    __slots__ = ("k0", "k1", "k2")
    def __init__(self, pwd):
        self.k0 = 0x12345678
        self.k1 = 0x23456789
        self.k2 = 0x34567890
        for c in pwd:
            self.update(c)

    def update(self, c):
        self.k0 = ((self.k0 >> 8) ^ CRCT[(self.k0 ^ c) & 0xFF]) & 0xFFFFFFFF
        self.k1 = (self.k1 + (self.k0 & 0xFF)) & 0xFFFFFFFF
        self.k1 = (self.k1 * 134775813 + 1) & 0xFFFFFFFF
        self.k2 = ((self.k2 >> 8) ^ CRCT[(self.k2 ^ ((self.k1 >> 24) & 0xFF)) & 0xFF]) & 0xFFFFFFFF

    def db(self):
        t = (self.k2 | 2) & 0xFFFF
        return ((t * (t ^ 1)) >> 8) & 0xFF

    def decrypt(self, data):
        out = bytearray()
        for b in data:
            c = self.db()
            p = b ^ c
            out.append(p)
            self.update(p)
        return bytes(out)

BASE = "/mnt/d/DSH/csapp/ctf-writeups/QuestionCTF2026"

def load_entry(path, want=None):
    b = open(path, "rb").read()
    off = 0
    while True:
        i = b.find(b"PK\x03\x04", off)
        if i < 0:
            return None
        ver, flag, meth, mt, md, crc, csz, usz, fnl, efl = struct.unpack_from("<HHHHHIIIHH", b, i + 4)
        name = b[i + 30:i + 30 + fnl].decode("latin1")
        d = i + 30 + fnl + efl
        if want is None or name == want:
            return dict(name=name, flag=flag, meth=meth, crc=crc, csz=csz, usz=usz, data=b[d:d + csz])
        off = i + 4

# ---------- step 0: validate the implementation against a 7-Zip-made archive ----------
print("=" * 60)
print("STEP 0  validate ZipCrypto implementation")
print("=" * 60)
t = load_entry(BASE + "/_test_enc.zip")
print("  entry        :", t["name"])
print("  flag=0x%04X method=%d crc=0x%08X csz=%d usz=%d" % (t["flag"], t["meth"], t["crc"], t["csz"], t["usz"]))
z = ZipCrypto(b"TESTPASS")
plain = z.decrypt(t["data"])
body = plain[12:]
print("  decrypted[0:12] :", binascii.hexlify(plain[:12]).decode())
print("  decrypted[11]   : 0x%02X   crc>>24 = 0x%02X" % (plain[11], (t["crc"] >> 24) & 0xFF))
print("  payload         :", body.decode("latin1"))
print("  crc computed    : 0x%08X  stored 0x%08X  %s" % (zlib.crc32(body) & 0xFFFFFFFF, t["crc"],
                                                      (zlib.crc32(body) & 0xFFFFFFFF) == t["crc"]))
OK = (zlib.crc32(body) & 0xFFFFFFFF) == t["crc"] and plain[11] == ((t["crc"] >> 24) & 0xFF)
print("  IMPLEMENTATION VALID:", OK)
if not OK:
    print("  >>> aborting: implementation is wrong")
    sys.exit(1)

# ---------- step 1: target entry ----------
print()
print("=" * 60)
print("STEP 1  target entry")
print("=" * 60)
e = load_entry(BASE + "/extracted/frist/final.zip", "flag/flag.txt")
D = e["data"]
CRC = e["crc"]
WANTB = (CRC >> 24) & 0xFF
print("  name=%s flag=0x%04X method=%d crc=0x%08X csz=%d usz=%d" % (e["name"], e["flag"], e["meth"], CRC, e["csz"], e["usz"]))
print("  data  :", binascii.hexlify(D).decode())
print("  need decrypted[11] == 0x%02X" % WANTB)

def test(pw):
    """returns plaintext if the CRC validates, else None"""
    z = ZipCrypto(pw)
    head = z.decrypt(D[:12])
    if head[11] != WANTB:
        return None
    z2 = ZipCrypto(pw)
    full = z2.decrypt(D)
    body = full[12:]
    if (zlib.crc32(body) & 0xFFFFFFFF) == CRC:
        return body
    return None

print()
print("=" * 60)
print("STEP 2  mask attack qctf2026 + 4 chars (verified by CRC)")
print("=" * 60)
CHARSETS = [
    ("digits", "0123456789"),
    ("lower", "abcdefghijklmnopqrstuvwxyz"),
    ("upper", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    ("lower+digit", "abcdefghijklmnopqrstuvwxyz0123456789"),
    ("alnum", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
    ("printable", "".join(chr(c) for c in range(32, 127))),
]
found = None
t0 = time.time()
for label, cs in CHARSETS:
    n = 0
    for combo in itertools.product(cs, repeat=4):
        pw = ("qctf2026" + "".join(combo)).encode()
        n += 1
        z = ZipCrypto(pw)
        if z.decrypt(D[:12])[11] != WANTB:
            continue
        z2 = ZipCrypto(pw)
        full = z2.decrypt(D)
        body = full[12:]
        if (zlib.crc32(body) & 0xFFFFFFFF) == CRC:
            found = (label, pw, body)
            break
    dt = time.time() - t0
    print("  charset %-12s tried %9d  elapsed %6.1fs  -> %s" % (label, n, dt, "HIT" if found else "nothing"))
    if found:
        break

if found:
    label, pw, body = found
    print()
    print("  *** PASSWORD FOUND ***")
    print("  charset   :", label)
    print("  password  :", pw.decode())
    print("  plaintext :", body.decode("latin1"))
else:
    print()
    print("  no 4-char suffix after 'qctf2026' works")
