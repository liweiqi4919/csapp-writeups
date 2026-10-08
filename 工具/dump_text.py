#!/usr/bin/env python3
# Dump PNG tEXt / zTXt / iTXt text chunks (they often hide hints).
import sys, struct, zlib

path = sys.argv[1] if len(sys.argv) > 1 else 'extracted/芙.png'
data = open(path, 'rb').read()

off = 8
while off + 8 <= len(data):
    ln = struct.unpack('>I', data[off:off + 4])[0]
    typ = data[off + 4:off + 8]
    body = data[off + 8:off + 8 + ln]
    if typ in (b'tEXt', b'zTXt', b'iTXt'):
        print('-' * 60)
        print('chunk :', typ.decode('latin1'), ' len =', ln, ' off = 0x%06X' % off)
        if typ == b'tEXt':
            kw, _, txt = body.partition(b'\x00')
            print('keyword:', kw.decode('latin1'))
            print('text   :', txt.decode('latin1'))
        elif typ == b'zTXt':
            kw, _, rest = body.partition(b'\x00')
            try:
                txt = zlib.decompress(rest[1:])
            except Exception as e:
                txt = b'<decompress failed: %s>' % str(e).encode()
            print('keyword:', kw.decode('latin1'))
            print('text   :', txt.decode('latin1', 'replace'))
        else:  # iTXt
            kw, _, rest = body.partition(b'\x00')
            comp_flag = rest[0]
            rest2 = rest[1:]
            lang, _, rest3 = rest2.partition(b'\x00')
            trans, _, text = rest3.partition(b'\x00')
            if comp_flag == 1:
                try:
                    text = zlib.decompress(text)
                except Exception as e:
                    text = b'<decompress failed: %s>' % str(e).encode()
            print('keyword  :', kw.decode('latin1'))
            print('language :', lang.decode('latin1'))
            print('transkey :', trans.decode('latin1'))
            print('compflag :', comp_flag)
            print('text     :', text.decode('utf-8', 'replace'))
    off += 12 + ln
    if typ == b'IEND':
        break
print('-' * 60)
