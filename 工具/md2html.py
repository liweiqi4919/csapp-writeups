#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2html.py -- 把 Markdown 转成一个能直接用浏览器 Ctrl+P 成 PDF 的 HTML。

用法:
    python3 md2html.py 输入.md 输出.html ["页面标题"]

只依赖 Python 标准库，不需要装任何东西。
支持: 标题 / 表格 / 代码块 / 列表 / 引用 / 图片 / 粗体斜体行内代码 / 分隔线 / 复选框
"""
import sys
import os
import re
import html

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Microsoft YaHei", "微软雅黑", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  font-size: 11.5pt;
  line-height: 1.75;
  color: #1a1a1a;
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 32px 60px;
  background: #fff;
}
h1 { font-size: 1.9em; border-bottom: 3px solid #2b6cb0; padding-bottom: .3em;
     margin: 0 0 1.2em; }
h2 { font-size: 1.4em; border-bottom: 1px solid #cbd5e0; padding-bottom: .25em;
     margin: 2em 0 .8em; page-break-after: avoid; }
h3 { font-size: 1.15em; margin: 1.6em 0 .6em; color: #2c5282;
     page-break-after: avoid; }
p  { margin: .7em 0; }
a  { color: #2b6cb0; text-decoration: none; }
code {
  font-family: Consolas, "Courier New", monospace;
  background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 3px;
  padding: .1em .35em; font-size: .92em; color: #b83280;
}
pre {
  background: #1e293b; color: #e2e8f0; border-radius: 6px;
  padding: 12px 14px; overflow-x: auto; page-break-inside: avoid;
  font-size: .88em; line-height: 1.55;
}
pre code { background: none; border: none; padding: 0; color: inherit; font-size: 1em; }
table {
  border-collapse: collapse; width: 100%; margin: 1em 0;
  font-size: .95em; page-break-inside: avoid;
}
th, td { border: 1px solid #cbd5e0; padding: 7px 10px; text-align: left;
         vertical-align: top; }
th { background: #edf2f7; font-weight: 600; }
tr:nth-child(even) td { background: #f9fafb; }
blockquote {
  border-left: 4px solid #90cdf4; background: #ebf8ff;
  margin: 1em 0; padding: .6em 1em; color: #2a4365;
}
blockquote p { margin: .3em 0; }
ul, ol { margin: .7em 0; padding-left: 1.8em; }
li { margin: .3em 0; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 2em 0; }
img { max-width: 100%; border: 1px solid #e2e8f0; border-radius: 4px;
      margin: .6em 0; }
.missing {
  display: block; border: 1px dashed #f6ad55; background: #fffaf0;
  color: #975a16; padding: 10px 14px; border-radius: 4px;
  font-size: .92em; margin: .6em 0;
}
.task { list-style: none; padding-left: .2em; }
.task li::before { content: ""; }
"""


def esc(text):
    return html.escape(text, quote=False)


def inline(text):
    """行内标记。先抽走行内代码，转义，再做其它替换。"""
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = esc(text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"<img src=\2 alt=\1>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)

    def unstash(m):
        return "<code>" + esc(codes[int(m.group(1))]) + "</code>"

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def is_table_sep(line):
    return bool(re.match(r"^\s*\|[\s:|-]+\|\s*$", line)) and "-" in line


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def convert(md_text, base_dir):
    lines = md_text.split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # ---- 代码块 ----
        if line.lstrip().startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + esc("\n".join(buf)) + "</code></pre>")
            continue

        # ---- 表格 ----
        if line.strip().startswith("|") and i + 1 < n and is_table_sep(lines[i + 1]):
            header = split_row(line)
            i += 2
            body = []
            while i < n and lines[i].strip().startswith("|"):
                body.append(split_row(lines[i]))
                i += 1
            t = ["<table><thead><tr>"]
            t += ["<th>%s</th>" % inline(c) for c in header]
            t.append("</tr></thead><tbody>")
            for row in body:
                t.append("<tr>")
                t += ["<td>%s</td>" % inline(c) for c in row]
                t.append("</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        # ---- 标题 ----
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2).strip()), lvl))
            i += 1
            continue

        # ---- 分隔线 ----
        if re.match(r"^\s*([-*_])\s*(\1\s*){2,}$", line):
            out.append("<hr>")
            i += 1
            continue

        # ---- 引用 ----
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and (lines[i].lstrip().startswith(">") or
                             (buf and lines[i].strip())):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = "<br>".join(inline(x) for x in buf if x.strip())
            out.append("<blockquote><p>%s</p></blockquote>" % inner)
            continue

        # ---- 列表 ----
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            tag = "ol" if ordered else "ul"
            items = []
            while i < n and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]):
                raw = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lines[i])
                cb = re.match(r"^\[([ xX])\]\s*(.*)$", raw)
                if cb:
                    mark = "☑" if cb.group(1).lower() == "x" else "☐"
                    items.append('<li class="task">%s %s</li>'
                                 % (mark, inline(cb.group(2))))
                else:
                    items.append("<li>%s</li>" % inline(raw))
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join(items), tag))
            continue

        # ---- 空行 ----
        if not line.strip():
            i += 1
            continue

        # ---- 段落 ----
        buf = []
        while i < n and lines[i].strip() and \
                not re.match(r"^\s*(#{1,6}\s|[-*+]\s|\d+\.\s|>|\||```)", lines[i]) and \
                not re.match(r"^\s*([-*_])\s*(\1\s*){2,}$", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append("<p>%s</p>" % inline(" ".join(buf)))
        else:
            i += 1

    body = "\n".join(out)

    # 图片不存在就换成提示框（避免 PDF 里出现空白裂图）
    def fix_img(m):
        src, alt = m.group(1), m.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        p = os.path.join(base_dir, src.replace("/", os.sep))
        if os.path.exists(p):
            return m.group(0)
        return ('<div class="missing">%s<br>图片未找到: %s</div>'
                % (esc(alt or "截图"), esc(src)))

    body = re.sub(r'<img src="([^"]+)" alt="([^"]*)">', fix_img, body)
    return body


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(
        os.path.basename(src))[0]
    with open(src, encoding="utf-8") as f:
        md = f.read()
    body = convert(md, os.path.dirname(os.path.abspath(src)))
    doc = ("<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
           "<meta charset=\"utf-8\">\n<title>%s</title>\n<style>%s</style>\n"
           "</head>\n<body>\n%s\n</body>\n</html>\n"
           % (esc(title), CSS, body))
    with open(dst, "w", encoding="utf-8") as f:
        f.write(doc)
    print("OK  %s  ->  %s  (%d 字节)" % (src, dst, len(doc.encode("utf-8"))))


if __name__ == "__main__":
    main()
