"""生成 game/cc/TSCharacters.txt 与 TSPhrases.txt（繁->简转换表）。

来源：OpenCC 的词典（TSCharacters / TSPhrases）。
注意两个坑，都必须处理，否则 SimpleCC 解析出来是空的、等于没有繁简转换：

1. OpenCC 原文件以 '#' 注释开头，而 SimpleCC 遇到「没有 \t 的行」会直接 break，
   所以注释行必须剔除；
2. **行尾必须是 LF**。SimpleCC 用 find_first_of("\r\n") 找行尾，遇到 CRLF 时
   只跳到 '\r'，下一轮的 key 就会以 '\n' 开头，导致除第一行外全部错位。

用法：
    python3 tools_local/make_cc_tables.py                # 下载并生成到 ./game/cc
    python3 tools_local/make_cc_tables.py --out DIR
"""
import argparse
import io
import json
import os
import urllib.request

FILES = ("TSCharacters.txt", "TSPhrases.txt")
API = "https://api.github.com/repos/BYVoid/OpenCC/contents/data/dictionary/%s?ref=master"


def fetch(name):
    req = urllib.request.Request(API % name, headers={"User-Agent": "kys-cc-fetch"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    import base64
    return base64.b64decode(data["content"]).decode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "game", "cc"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    for name in FILES:
        text = fetch(name)
        lines = []
        for line in text.splitlines():
            if not line or line.startswith("#") or "\t" not in line:
                continue
            lines.append(line)
        out = os.path.join(args.out, name)
        # 关键：二进制写入 + LF，避免 Windows 下变成 CRLF
        io.open(out, "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
        print("%s: %d 条" % (out, len(lines)))


if __name__ == "__main__":
    main()
