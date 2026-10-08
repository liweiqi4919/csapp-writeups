import struct, binascii, itertools, sys

# ---- ZipCrypto implementation (PKWARE traditional encryption) ----
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
    def __init__(self, pwd):
        self.k0 = 0x12345678
        self.k1 = 0x23456789
        self.k2 = 0x34567890
        for ch in pwd:
            self.update(ch)

    def update(self, c):
        self.k0 = (self.k0 >> 8) ^ CRCT[(self.k0 ^ c) & 0xFF]
        self.k0 &= 0xFFFFFFFF
        self.k1 = (self.k1 + (self.k0 & 0xFF)) & 0xFFFFFFFF
        self.k1 = (self.k1 * 134775813 + 1) & 0xFFFFFFFF
        self.k2 = (self.k2 >> 8) ^ CRCT[(self.k2 ^ ((self.k1 >> 24) & 0xFF)) & 0xFF]
        self.k2 &= 0xFFFFFFFF

    def decrypt_byte(self):
        temp = (self.k2 | 2) & 0xFFFF
        return ((temp * (temp ^ 1)) >> 8) & 0xFF

    def decrypt(self, data):
        out = bytearray()
        for b in data:
            c = self.decrypt_byte()
            out.append(b ^ c)
            self.update(b ^ c)
        return bytes(out)

def crc32_of(data):
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF

# ---- target entry ----
with open("/mnt/d/DSH/csapp/ctf-writeups/frist.zip", "rb") as f:
    outer = f.read()
with open("/mnt/d/DSH/csapp/ctf-writeups/QuestionCTF2026/extracted/frist/final.zip", "rb") as f:
    inner = f.read()

i = inner.find(b"PK\x03\x04", 4)
ver, flag, meth, mt, md, crc, csz, usz, fnl, efl = struct.unpack_from("<HHHHHIIIHH", inner, i + 4)
name = inner[i + 30:i + 30 + fnl].decode("latin1")
dstart = i + 30 + fnl + efl
data = inner[dstart:dstart + csz]

print("entry           :", name)
print("flag            : 0x%04X  method=%d" % (flag, meth))
print("crc             : 0x%08X" % crc)
print("compressed size :", csz, " uncompressed size:", usz)
print("data hex        :", binascii.hexlify(data).decode())
print("crc high byte   : 0x%02X   <- the decrypted byte#11 must equal this" % ((crc >> 24) & 0xFF))
print()

def try_pwd(pw):
    if isinstance(pw, str):
        pw = pw.encode("utf-8", "replace")
    z = ZipCrypto(pw)
    head = z.decrypt(data[:12])
    ok = head[11] == ((crc >> 24) & 0xFF)
    return ok, head

cands = [
    "qctf2026", "qctf2026????", "qctf2026?", "qctf2026??", "qctf2026???",
    "QCTF2026", "Qctf2026", "qctf", "qctf2026!", "?ctf2026", "?CTF2026",
    "kalsaaa", "Kalsaaa", "kalsaa", "kalsaaa123",
    "123456", "password", "admin", "flag", "ctf", "ctf2026", "CTF2026",
    "questionctf", "QuestionCTF", "questionctf2026", "?CTF", "?ctf",
    "", "youaresosmart", "You are so smart", "this_is_a_fake_flag",
    "final", "final.zip", "frist", "frist.zip", "压缩包",
    "qctf2026@@@@", "qctf2026####", "qctf2026....", "qctf2026____",
    "qctf2026    ", "qctf2026    ".strip(), "qctf2026{", "qctf2026}",
]

print("=== candidate passwords (only the 12-byte check is tested) ===")
any_ok = False
for pw in cands:
    ok, head = try_pwd(pw)
    mark = "  <<<< MATCH" if ok else ""
    if ok:
        any_ok = True
    print("  %-22r check=0x%02X  %s%s" % (pw, head[11], "OK" if ok else "--", mark))

print()
print("=== mask attack: qctf2026 + 4 chars ===")
CHARLETS = [
    ("digits", "0123456789"),
    ("lower", "abcdefghijklmnopqrstuvwxyz"),
    ("lower+digit", "abcdefghijklmnopqrstuvwxyz0123456789"),
    ("alnum", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
    ("printable-ascii", "".join(chr(c) for c in range(32, 127))),
]
want = ((crc >> 24) & 0xFF)
found = None
for label, cs in CHARLETS:
    n = 0
    for combo in itertools.product(cs, repeat=4):
        pw = "qctf2026" + "".join(combo)
        z = ZipCrypto(pw.encode("utf-8"))
        head = z.decrypt(data[:12])
        n += 1
        if head[11] == want:
            print("  FOUND with charset %s : %r" % (label, pw))
            found = pw
            break
    print("  charset %-16s tried %d combos -> %s" % (label, n, "hit" if found else "no hit"))
    if found:
        break

if found:
    z = ZipCrypto(found.encode())
    plain = z.decrypt(data)
    body = plain[12:]
    print()
    print("  plaintext length :", len(body))
    print("  crc match        :", "0x%08X" % crc32_of(body), "vs stored 0x%08X" % crc, crc == crc32_of(body))
    print("  plaintext hex    :", binascii.hexlify(body).decode())
    print("  plaintext ascii  :", "".join(chr(c) if 32 <= c < 127 else "." for c in body))
else:
    print()
    print("  mask attack found nothing")
