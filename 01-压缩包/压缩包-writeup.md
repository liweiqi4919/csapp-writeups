# Misc 压缩包

| 项目 | 内容 |
|---|---|
| **比赛** | ?CTF 2026 |
| **方向** | Misc |
| **题目名** | 压缩包 |
| **分值 / 难度** | 205 → 204（动态计分） / 简单 |
| **解题日期** | 2026.10.04 |
| **耗时** | 约 2 小时 |
| **最终 flag** | `?CTF{Thi3_is_@_ez_z1p!}` |

---

## 一、题目给了什么

- **附件**：`frist.zip`（836 字节，注意作者把 `first` 拼成了 `frist`）
- **题目描述**：这是一个神秘的压缩包，我真加密了吗？我真没加密吗？
- **提示**：`tips: flag格式应为 ?CTF{xxx}`

**描述里的双关**：「我真加密了吗？我真没加密吗？」—— 这句话直接告诉你**加密是假的**。

---

## 二、我的第一反应
当我打开这个压缩包 它显示要密码，这对第一次做CTF的我来说一头雾水。
，
## 三、分析过程

### 第 1 步：看这个 zip 里有什么

```bash
7z l -slt frist.zip
```

**结果**：

```
Path = frist/final.zip                     Size = 317   Packed Size = 156   Method = Deflate   Encrypted = +
Path = frist/Is_this_a_real_flag.txt       Size = 160   Packed Size = 130   Method = Deflate   Encrypted = +
```

**判断**：两个文件都标着 `Encrypted = +`（声称加密了），**但 `Packed Size` 比 `Size` 小** —— 说明数据被**真的压缩过**，也就是**数据是明文**。

> 🔑 **关键推理**：真加密过的数据是不可压缩的（密文看起来就是随机数）。
> 如果它又被压缩、`Packed < Size`，那**它压根没被加密**。
> **只有标志位在撒谎。**

### 第 2 步：直接看字节（用 xxd）

```bash
xxd frist.zip | head -30
```

**看到的结构**：

| 偏移 | 内容 |
|---|---|
| `0x0000` | 本地头 `frist/`（目录项），标志 `0x0000` |
| `0x0044` | 本地头 `frist/final.zip`，**标志 `0x0009`** |
| `0x013D` | 本地头 `frist/Is_this_a_real_flag.txt`，**标志 `0x0009`** |
| `0x022A` | 中央目录开始 |

**标志位 `0x0009` 的两个 bit**：

```
0x0009 = 0000 0000 0000 1001
                bit3 ↑        ↑ bit0
bit0 = 1  →  "这个文件加密了"   ← 撒谎的那个
bit3 = 1  →  "CRC 和大小写在数据后面的数据描述符里"（合法写法）
```

⚠️ **所以文件头里那几个「填 0」的字段不是缺失，是 bit3 的合法写法。**

### 第 3 步：证明它是伪加密

**测试 A：直接从数据起点按 raw deflate 解压**

```python
# 从数据起点开始解
zlib.decompressobj(-15).decompress(data)
```

**结果：两个文件都解压成功！**

```
frist/final.zip              → 317 字节，开头 50 4B 03 04（又是一个 ZIP！）
frist/Is_this_a_real_flag.txt → 160 字节，开头 "You are so smart"
```

**测试 B：跳过 12 字节「加密头」再解压**

**结果：两个都失败**（`Unknown block type. Stream might be corrupted.`）

**判断**：**压根没有加密头 —— 数据从来没被加密过。**

**交叉验证**：解出来的大小 317 / 160，和中央目录声称的 317 / 160 **分毫不差**。

### 第 4 步：修改标志位，正常解压

把 4 个位置的标志位从 `0x09` 清成 `0x08`（`flag & 0xFE`）：

```python
for off in (0x004A, 0x0143, 0x027E, 0x02D3):
    data[off] &= 0xFE
```

存成 `frist_fixed.zip` → **7-Zip 不再要密码，正常解压**。

解出：

```
final.zip                    (317 字节)
Is_this_a_real_flag.txt      (160 字节)
```

### 第 5 步：读诱饵文件

`Is_this_a_real_flag.txt` 全文：

```

You are so smart ，

flag{this_is_a_fake_flag}

but there is a string of mysterious characters here:

qctf2026????

do you know what it is? qwq

```

**这是诱饵**：明写的 `flag{this_is_a_fake_flag}` 是假的（占位符），但**最后给了真线索**。

> ⚠️ **`flag{...}` ≠ `?CTF{...}`** —— 提交前一定要对照题目给的格式。

**提示的含义**：`qctf2026????` → 密码是 12 位，**前 8 位已知，后 4 位未知**。

### 第 6 步：看内层 final.zip

```bash
7z l -slt final.zip
```

```
Path = flag/flag.txt    Size = 23    Packed Size = 35    Method = ZipCrypto Store    Encrypted = +    CRC = 5A52DCC3
```

**这里 `Packed = Size + 12`：**

```
35 = 23 + 12
     ↑
   12 字节 = ZipCrypto 的加密头
```

**对比外层的 `Packed < Size`（真压缩）—— 这次是 `Packed = Size + 12`，所以是真加密。**

**为了确认这个判断，我造了一个对照样本：**

```bash
7z a -tzip -pTESTPASS -mem=ZipCrypto _test_enc.zip _test_plain.txt
# 明文 31 字节 → Packed Size = 43 = 31 + 12，Method = ZipCrypto Store，标志 0x0001
```

**结构完全一致 → 确认内层是真 ZipCrypto，必须有密码。**

### 第 7 步：掩码爆破密码

**用 Python 手写 ZipCrypto 解密**（密钥初始化 + 三密钥流）：

```python
class ZipCrypto:
    def __init__(self, pwd):
        self.k0, self.k1, self.k2 = 0x12345678, 0x23456789, 0x34567890
        for c in pwd: self.update(c)
    def update(self, c):
        self.k0 = (self.k0 >> 8) ^ CRCT[(self.k0 ^ c) & 0xFF]
        self.k1 = (self.k1 + (self.k0 & 0xFF)) * 134775813 + 1 & 0xFFFFFFFF
        self.k2 = (self.k2 >> 8) ^ CRCT[(self.k2 ^ (self.k1 >> 24)) & 0xFF]
    def db(self):
        t = (self.k2 | 2) & 0xFFFF
        return ((t * (t ^ 1)) >> 8) & 0xFF
```

**先验证实现正确性**（用第 6 步造的对照样本，已知密码 `TESTPASS`）：

```
decrypted[11]  : 0x0A   crc>>24 = 0x0A     ← 对上了
payload        : ?CTF{this_is_a_known_test_flag}
crc computed   : 0x0AF157C7  stored 0x0AF157C7  True
IMPLEMENTATION VALID: True
```

**验证通过，再对目标爆破。**

**结果**：

```
charset digits       tried     10000  → nothing
charset lower        tried    456976  → nothing
charset upper        tried    456976  → nothing
charset lower+digit  tried    314140  → HIT

password  : qctf2026g0od
plaintext : ?CTF{Thi3_is_@_ez_z1p!}
```

**用 7-Zip 输密码解压 → 拿到 flag → 提交成功。**

---

## 四、卡住的地方

一开始看到CTF2026后又接四个问号是以为是答案 结果输上去却不对 后来我又试着去掉问号还是不行，最后是ai帮我写了个脚本暴力得出最终答案。
---

## 五、关键截图

<!-- 放在同目录 assets/ 文件夹里 -->

| 文件 | 内容 |
|---|---|
| `assets/01-7zip-list.png` | 7-Zip 列出外层记录，两个都标 `Encrypted = +` |
| `assets/02-xxd-header.png` | xxd 看本地头，标志位是 `09 00` |
| `assets/03-decoy-txt.png` | 诱饵 txt 全文 |
| `assets/04-inner-7zip.png` | 内层 `Packed = 35 / Size = 23` |
| `assets/05-crack-result.png` | 爆破脚本输出，密码 `qctf2026g0od` |
| `assets/06-flag.png` | 解出来的 flag |
| `assets/07-submitted.png` | 平台「提交 flag 成功」 |

---

## 六、最终解法（给别人的版本）

**核心原理**：

> **ZIP 的「加密标志位」只是一个声明，不代表数据真的被加密了。**
>
> - **伪加密**：标志位置 1，但数据是明文 → 把标志位改回 0 就能开
> - **真加密**：标志位置 1，数据真的被 ZipCrypto 加密 → 必须有密码
>
> **怎么区分？看 `Packed Size` 和 `Size` 的关系：**
> - `Packed < Size`（或 `Packed ≈ Size`）→ 数据被压缩过 → **伪加密，数据是明文**
> - `Packed = Size + 12` → 多出一个 12 字节的加密头 → **真加密**

**完整步骤**：

1. `7z l -slt frist.zip` → 两个记录都标 `Encrypted = +`，但 `Packed < Size` → **伪加密**
2. `xxd frist.zip` → 本地头标志是 `0x0009`，bit0 在撒谎
3. 直接从数据起点 raw deflate 解压 → **成功**，证明没有加密头
4. 把 4 处标志位 `0x09 → 0x08`，保存为新 zip → 正常解压
5. 读诱饵 txt → 得到提示 `qctf2026????`（前 8 位是密码前缀，后 4 位未知）
6. `7z l -slt final.zip` → `Packed = 35`、`Size = 23` → **35 = 23 + 12 → 真 ZipCrypto**
7. 掩码爆破 `qctf2026` + 4 位（digits → lower → upper → lower+digit）
8. 用 **CRC32 全 32 位比对**判定候选（**不要用 8 位的检查字节**）
9. 密码 `qctf2026g0od` → 7-Zip 解压 → flag

**关键命令 / 代码**：

```bash
# 看 zip 结构
7z l -slt frist.zip

# 看字节
xxd frist.zip | head -30

# 造一个已知密码的 ZipCrypto 对照样本（验证自己的解密实现）
7z a -tzip -pTESTPASS -mem=ZipCrypto _test_enc.zip _test_plain.txt
```

```python
# 清标志位（伪加密 → 正常）
data = bytearray(open('frist.zip','rb').read())
for off in (0x004A, 0x0143, 0x027E, 0x02D3):
    data[off] &= 0xFE          # 清掉 bit0
open('frist_fixed.zip','wb').write(data)
```

```python
# 判定候选密码：用 CRC32，不要用检查字节
z = ZipCrypto(pw)
full = z.decrypt(D)
if zlib.crc32(full[12:]) & 0xFFFFFFFF == STORED_CRC:   # ✅ 唯一可信判据
    ...
```

---

## 七、学到了什么

| 学到的东西 | 以后能用在 |
|---|---|
| **标志位/文件头是「声明」，不是「事实」** | 所有文件格式题、隐写、流量分析 |
| **`Packed` vs `Size` 的关系能识破伪加密** | 一切 ZIP 相关的 Misc 题 |
| **ZIP 本地头的字段布局**（偏移+长度=下一字段） | 解析任何二进制格式（PNG / ELF / PE） |
| **小端序**：`14 00` 是 20，不是 5120 | CSAPP §2.1.4、所有逆向题 |
| **掩码爆破（mask attack）** | 密码题、哈希题、所有「部分已知」的爆破 |
| **校验位的可信度 = 位数**（8 位 → 1/256 假阳性） | 写任何爆破脚本 |
| **`flag{...}` ≠ 题目要求的格式** | 每次提交前都要核对 |

**涉及的知识点**：

- [x] 新工具：**7-Zip CLI**（`7z l -slt`）、**xxd**（十六进制查看）
- [x] 新命令：`7z l -slt`、`7z a -tzip -p... -mem=ZipCrypto`
- [x] 新概念：**ZIP 伪加密**、**ZipCrypto 加密头**、**掩码爆破**、**CRC32 校验**

**CSAPP / 课程对应**：

| 这题涉及的 | CSAPP 章节 |
|---|---|
| 小端序、字节序 | **§2.1.4 字节顺序**（L0-③ 已实测过） |
| 十六进制、位运算（`& 0xFE`） | **§2.1 信息的存储**（L0-② 已实测过） |
| CRC 校验、碰撞概率 | **§2.4 / §9.6**（校验和的权衡） |
| 解析二进制格式 | **§3 程序的机器级表示** |

---

## 八、一句话总结

在面对伪加密题时，应先用010editor观看其字符，找到伪加密字节所在改掉他，8 位检查位每 256 次就会骗你一次。
---

*存放位置：`D:\DSH\csapp\ctf-writeups\QuestionCTF2026\压缩包.md`*
