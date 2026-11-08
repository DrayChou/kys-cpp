"""
kys-cpp 资源转换：把 DOS 版《金庸群侠传》的 GRP/IDX 转成复刻版需要的 PNG 贴图组 + index.ka，
并把 TALK.GRP 转成 talkutf8.txt。

用法:
  python3 convert_dos_res.py --dos <DOS数据目录> --jyol <jyol数据目录> --out <game/resource>

  不给参数时用脚本里的默认路径（Windows 本机路径）。
"""
import argparse
import os
import struct
import sys
import zlib
import binascii

DOS = r"E:\Games\kys-dos-data"
JYOL = r"E:\Games\jyol-assets\data"
OUT = r"E:\Games\kys-cpp\game\resource"

PALETTE = None


def load_palette():
    """MMAP.COL: 256 * 3 字节 RGB"""
    global PALETTE
    with open(os.path.join(DOS, "MMAP.COL"), "rb") as f:
        raw = f.read()
    PALETTE = [(min(255, 4 * raw[i * 3]), min(255, 4 * raw[i * 3 + 1]), min(255, 4 * raw[i * 3 + 2]))
               for i in range(256)]


def read_idx(path):
    with open(path, "rb") as f:
        raw = f.read()
    n = len(raw) // 4
    return list(struct.unpack("<%di" % n, raw[:n * 4]))


def _plausible(w, h):
    return 1 < w <= 300 and 1 < h <= 300


def _header_mode(grp, spans):
    """判断这批记录的 8 字节头在开头还是结尾（部分 FIGHT*.GRP 是放在结尾的）"""
    score_start = score_end = 0
    for start, end in spans[:40]:
        if end - start <= 8:
            continue
        w, h = struct.unpack("<hh", grp[start:start + 4])
        if _plausible(w, h):
            score_start += 1
        w, h = struct.unpack("<hh", grp[end - 8:end - 4])
        if _plausible(w, h):
            score_end += 1
    return "end" if score_end > score_start else "start"


def decode_image(grp, start, end, pal, header="start"):
    """一条 GRP 记录 -> (Image, xoff, yoff)；格式见 tools/xia/grpidx.cpp"""
    if end - start <= 8:
        return None
    if header == "end":
        w, h, xoff, yoff = struct.unpack("<hhhh", grp[end - 8:end])
        end -= 8
    else:
        w, h, xoff, yoff = struct.unpack("<hhhh", grp[start:start + 8])
        start += 8
    if w <= 0 or h <= 0 or w > 1023 or h > 1023:
        return None
    buf = bytearray(w * h * 4)
    p = start
    for y in range(h):
        if p >= end:
            break
        row_len = grp[p]
        row_start = p
        p += 1
        if row_len == 0:
            continue
        x = 0
        while True:
            if p >= end:
                break
            x += grp[p]
            if x >= w:
                break
            p += 1
            if p >= end:
                break
            solid = grp[p]
            p += 1
            for _ in range(solid):
                if p >= end or x >= w:
                    break
                if grp[p] != 0:
                    c = pal[grp[p]]
                    o = (y * w + x) * 4
                    buf[o] = c[0]
                    buf[o + 1] = c[1]
                    buf[o + 2] = c[2]
                    buf[o + 3] = 255
                p += 1
                x += 1
            if x >= w:
                break
            if p - row_start >= row_len:
                break
    return (w, h, buf), xoff, yoff


def write_png(path, w, h, rgba):
    """最小 PNG 写出（RGBA8，无滤波），不依赖 Pillow"""
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    with open(path, "wb") as f:
        f.write(bytes([137, 80, 78, 71, 13, 10, 26, 10]))
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 6)))
        f.write(chunk(b"IEND", b""))


def rotate_palette(pal, begin, end):
    """0xe0-0xe7 / 0xf4-0xfc 区段轮换，用于水面等动画帧"""
    p = list(pal)
    tmp = p[end]
    for j in range(end, begin, -1):
        p[j] = p[j - 1]
    p[begin] = tmp
    return p


def convert_group(idx_path, grp_path, out_dir, animate=False, palette=None):
    """GRP/IDX -> out_dir/N.png (+ N_1.png .. N_8.png) + index.ka"""
    if not (os.path.exists(idx_path) and os.path.exists(grp_path)):
        print("  跳过（文件缺失）:", os.path.basename(grp_path))
        return 0
    pal = palette or PALETTE
    idx = [0] + read_idx(idx_path)
    with open(grp_path, "rb") as f:
        grp = f.read()
    count = len(idx) - 1
    spans = [(idx[m], idx[m + 1]) for m in range(count) if idx[m + 1] > idx[m]]
    header = _header_mode(grp, spans)
    os.makedirs(out_dir, exist_ok=True)
    offsets = [0] * (count * 2)
    written = 0
    for m in range(count):
        start, end = idx[m], idx[m + 1]
        if end <= 0 or end > len(grp) or end - start <= 8:
            continue
        got = decode_image(grp, start, end, pal, header)
        if not got:
            continue
        img, xoff, yoff = got
        offsets[m * 2] = xoff
        offsets[m * 2 + 1] = yoff
        # 判断是否需要做调色板动画帧
        use_pal = pal
        frames = 1
        if animate:
            data = grp[start + 8:end]
            has_a = any(0xe0 <= b <= 0xe7 for b in data)
            has_b = any(0xf4 <= b <= 0xfc for b in data)
            frames = 8 if has_a else (9 if has_b else 1)
        for n in range(frames):
            if n == 0:
                cur, name = img, "%d.png" % m
            else:
                use_pal = rotate_palette(use_pal, 0xE0, 0xE7)
                use_pal = rotate_palette(use_pal, 0xF4, 0xFC)
                got2 = decode_image(grp, start, end, use_pal, header)
                if not got2:
                    break
                cur, name = got2[0], "%d_%d.png" % (m, n)
            write_png(os.path.join(out_dir, name), cur[0], cur[1], cur[2])
            written += 1
    with open(os.path.join(out_dir, "index.ka"), "wb") as f:
        f.write(struct.pack("<%dh" % len(offsets), *offsets))
    print("  %-28s %4d 张 -> %s" % (os.path.basename(grp_path), written, os.path.basename(out_dir)))
    return written


def convert_talk():
    """TALK.GRP/IDX -> talkutf8.txt（整段 XOR 0xFF，CP950 -> UTF-8，去掉 * 和换行）"""
    idx_path = os.path.join(DOS, "TALK.IDX")
    grp_path = os.path.join(DOS, "TALK.GRP")
    idx = read_idx(idx_path)
    with open(grp_path, "rb") as f:
        buf = bytearray(f.read())
    limit = idx[-1] if idx else len(buf)
    for i in range(min(limit, len(buf))):
        if buf[i]:
            buf[i] ^= 0xFF
    lines = []
    for k in range(len(idx) - 1):
        s, e = idx[k], idx[k + 1]
        if e <= s:
            lines.append("")
            continue
        raw = bytes(buf[s:e]).split(b"\x00")[0]
        try:
            text = raw.decode("cp950", errors="replace")
        except Exception:
            text = raw.decode("latin1")
        text = text.replace("*", "").replace("\r", "").replace("\n", "").replace('"', "”")
        lines.append(text)
    out = os.path.join(OUT, "talkutf8.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("  TALK.GRP -> talkutf8.txt  %d 条对话" % len(lines))



def convert_fights():
    """FIGHTxxx.GRP/IDX -> fight/fightXXX/（DOS 批处理里最后一个参数是 0）"""
    import glob
    files = sorted(glob.glob(os.path.join(DOS, "FIGHT*.GRP")))
    n = 0
    for g in files:
        base = os.path.splitext(os.path.basename(g))[0]          # FIGHT017
        idx = os.path.join(DOS, base + ".IDX")
        if not os.path.exists(idx):
            continue
        name = "fight" + base[5:]                                  # fight017
        n += convert_group(idx, g, os.path.join(OUT, "fight", name), animate=False)
    print("  战斗贴图共 %d 张" % n)


def make_title_background():
    """TITLE.BIG(320x200 8位) + MMAP.COL -> title/153.png、154.png（游戏要的 1024x640 标题背景）"""
    src = os.path.join(DOS, "TITLE.BIG")
    if not os.path.exists(src):
        src = os.path.join(DOS, "title.big")
    if not os.path.exists(src):
        print("  跳过标题背景（没有 TITLE.BIG）")
        return
    raw = open(src, "rb").read()
    W, H = 320, 200
    if len(raw) < W * H:
        print("  跳过标题背景（TITLE.BIG 尺寸不对）")
        return
    SW, SH = 1024, 640
    buf = bytearray(SW * SH * 4)
    for y in range(SH):
        sy = y * H // SH
        base = sy * W
        row = y * SW
        for x in range(SW):
            c = PALETTE[raw[base + (x * W // SW)]]
            o = (row + x) * 4
            buf[o] = c[0]
            buf[o + 1] = c[1]
            buf[o + 2] = c[2]
            buf[o + 3] = 255
    out = os.path.join(OUT, "title")
    os.makedirs(out, exist_ok=True)
    for name in ("153.png", "154.png"):
        write_png(os.path.join(out, name), SW, SH, buf)
    print("  TITLE.BIG -> title/153.png、154.png（%dx%d）" % (SW, SH))


def main():
    global DOS, JYOL, OUT
    ap = argparse.ArgumentParser(description="DOS 版金庸群侠传资源 -> kys-cpp 资源目录")
    ap.add_argument("--dos", default=DOS, help="DOS 原版数据目录（含 KDEF.GRP/TALK.GRP/MMAP.COL/*.002）")
    ap.add_argument("--jyol", default=JYOL, help="jyol 数据目录（补 smap.grp / thing.grp，可缺省）")
    ap.add_argument("--out", default=OUT, help="输出目录（游戏的 game/resource）")
    args = ap.parse_args()
    DOS, JYOL, OUT = args.dos, args.jyol, args.out

    if not os.path.isdir(DOS):
        sys.exit("找不到 DOS 数据目录：%s（用 --dos 指定）" % DOS)
    if not os.path.isfile(os.path.join(DOS, "TALK.GRP")) and not os.path.isfile(os.path.join(DOS, "talk.grp")):
        print("警告：%s 里没有 TALK.GRP/talk.grp，对话将不会生成" % DOS)
    if not os.path.isdir(JYOL):
        print("提示：没有 --jyol 目录，smap（场景图）和 item（物品图标）会缺失")

    load_palette()
    os.makedirs(OUT, exist_ok=True)

    print("[1/3] 拷贝原始数据文件")
    import shutil
    for name in ["KDEF.GRP", "KDEF.IDX", "WAR.STA", "HERO.STA", "MMAP.COL",
                 "EARTH.002", "SURFACE.002", "BUILDING.002", "BUILDX.002", "BUILDY.002",
                 "WARFLD.GRP", "WARFLD.IDX", "CLOUD.GRP", "CLOUD.IDX"]:
        src = os.path.join(DOS, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(OUT, name.lower()))
    print("  ok")

    print("[2/3] 转换贴图组")
    convert_group(os.path.join(DOS, "TITLE.IDX"), os.path.join(DOS, "TITLE.GRP"), os.path.join(OUT, "title"))
    convert_group(os.path.join(DOS, "HDGRP.IDX"), os.path.join(DOS, "HDGRP.GRP"), os.path.join(OUT, "head"))
    convert_group(os.path.join(JYOL, "thing.idx"), os.path.join(JYOL, "thing.grp"), os.path.join(OUT, "item"))
    convert_group(os.path.join(DOS, "MMAP.IDX"), os.path.join(DOS, "MMAP.GRP"), os.path.join(OUT, "mmap"), animate=True)
    convert_group(os.path.join(JYOL, "smap.idx"), os.path.join(JYOL, "smap.grp"), os.path.join(OUT, "smap"), animate=True)
    convert_group(os.path.join(DOS, "WARFLD.IDX"), os.path.join(DOS, "WARFLD.GRP"), os.path.join(OUT, "battle-earth"))
    convert_group(os.path.join(DOS, "EFT.IDX"), os.path.join(DOS, "EFT.GRP"), os.path.join(OUT, "eft"))

    convert_fights()

    make_title_background()

    print("[3/3] 转换对话")
    convert_talk()

    total = sum(len(files) for _, _, files in os.walk(OUT))
    print("完成：resource 下共 %d 个文件" % total)


if __name__ == "__main__":
    main()
