"""XMI(XMIDI) -> SMF(.mid)：把 DOS 版《金庸群侠传》GAME01..24.XMI 转成标准 MIDI。

这套 XMIDI 的特点：**delta 为 0 时直接省略**，所以事件流里既有
  `08 90 2b 67`（delta=8 + note-on）
也有
  `b0 00 00`（无 delta + control change）
而 `81 1e b2 5d 32` 里的 `81 1e` 又是两字节 delta。

判别方法：通道事件的数据字节必定 < 0x80。
  - 下一字节 < 0x80        → 一定是 delta
  - 下一字节 >= 0x80       → 先按「这是状态字节（delta=0）」试，
                            若它的数据字节里出现 >= 0x80，才判定为两字节 delta
"""
import os
import struct

DOS = r"E:\Games\kys-dos-data"
OUT = r"E:\Games\kys-cpp\game\music"

CHANNEL_VALID = set(range(0x80, 0xF0)) | {0xF0, 0xF7, 0xFF}


def find_chunks(buf, tag):
    out = []
    i = 0
    while True:
        i = buf.find(tag, i)
        if i < 0:
            break
        size = struct.unpack(">I", buf[i + 4:i + 8])[0]
        out.append(buf[i + 8:i + 8 + size])
        i += 8
    return out


def vlq_write(v):
    out = bytearray([v & 0x7F])
    v >>= 7
    while v:
        out.insert(0, 0x80 | (v & 0x7F))
        v >>= 7
    return bytes(out)


def try_event(ev, pos, last_status):
    """从 pos 开始按「无 delta」解析一个事件，成功返回 (status, data, newpos)"""
    n = len(ev)
    if pos >= n:
        return None
    status = ev[pos]
    if status not in CHANNEL_VALID:
        return None
    p = pos + 1
    if status == 0xFF:
        if p + 1 >= n:
            return None
        mtype = ev[p]
        length = ev[p + 1]
        p += 2
        if p + length > n:
            return None
        return ("meta", mtype, ev[p:p + length], p + length)
    if status in (0xF0, 0xF7):
        if p >= n:
            return None
        length = ev[p]
        p += 1
        if p + length > n:
            return None
        return ("sysex", status, ev[p:p + length], p + length)
    want = 1 if (status & 0xF0) in (0xC0, 0xD0) else 2
    if p + want > n:
        return None
    data = ev[p:p + want]
    if any(b >= 0x80 for b in data):        # 数据字节必须 < 0x80
        return None
    return ("chan", status, list(data), p + want)


def xmi_to_mid(data):
    evnts = find_chunks(data, b"EVNT")
    if not evnts:
        return None
    ev = evnts[0]
    n = len(ev)
    track = bytearray()
    pos = 0
    last_status = 0
    guard = 0
    while pos < n and guard < 100000:
        guard += 1
        delta = None
        if ev[pos] < 0x80:
            delta = ev[pos]
            pos += 1
        else:
            # 先试「无 delta」：下一个字节直接是状态
            cand = try_event(ev, pos, last_status)
            if cand is not None:
                delta = 0
            else:
                if pos + 1 >= n:
                    break
                delta = ((ev[pos] & 0x7F) << 7) | (ev[pos + 1] & 0x7F)
                pos += 2
        got = try_event(ev, pos, last_status)
        if got is None:
            break
        pos = got[-1]
        kind = got[0]
        if kind == "meta":
            _, mtype, body, _ = got
            track += vlq_write(delta) + bytes([0xFF, mtype, len(body)]) + body
            if mtype == 0x2F:
                break
            continue
        if kind == "sysex":
            _, status, body, _ = got
            track += vlq_write(delta) + bytes([status, len(body)]) + body
            continue
        _, status, body, _ = got
        last_status = status
        track += vlq_write(delta) + bytes([status] + body)

    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 96)
    return header + b"MTrk" + struct.pack(">I", len(track)) + bytes(track)


def main():
    os.makedirs(OUT, exist_ok=True)
    ok = 0
    for f in sorted(os.listdir(DOS)):
        if not f.upper().endswith(".XMI"):
            continue
        num = "".join(ch for ch in f if ch.isdigit())
        if not num:
            continue
        mid = xmi_to_mid(open(os.path.join(DOS, f), "rb").read())
        if not mid:
            print("跳过", f)
            continue
        open(os.path.join(OUT, "%d.mid" % int(num)), "wb").write(mid)
        ok += 1
    print("转换 %d 首 XMI -> MID" % ok)


if __name__ == "__main__":
    main()
