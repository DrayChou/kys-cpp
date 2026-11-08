"""通过 kys-cpp 自带的 MCP(stdio) 接口驱动游戏：读 UI 状态、按键、截图。
用法:
  python mcp_drive.py state
  python mcp_drive.py key confirm
  python mcp_drive.py sequence "confirm wait down confirm"
  python mcp_drive.py shot out.png
"""
import json
import subprocess
import sys
import time
import os
import base64

EXE = r"E:\Games\kys-cpp\dist\kys.exe"
GAME = r"E:\Games\kys-cpp\game"
WORKDIR = r"E:\Games\kys-cpp"


class Mcp:
    def __init__(self):
        env = dict(os.environ)
        env["PATH"] = r"E:\Games\kys-cpp\dist;" + env.get("PATH", "")
        self.p = subprocess.Popen([EXE, GAME, "--mcp-stdio"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  cwd=WORKDIR, env=env, bufsize=1, text=True, encoding="utf-8")
        self.msg_id = 0
        self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "driver", "version": "1.0"}})
        self.notify("notifications/initialized")

    def send(self, obj):
        if "id" not in obj:
            self.p.stdin.write(json.dumps(obj) + "\n")
            self.p.stdin.flush()
            return None
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()
        want = obj["id"]
        t0 = time.time()
        while time.time() - t0 < 60:
            line = self.p.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if msg.get("id") == want:
                return msg
        return None

    def call(self, method, params=None):
        self.msg_id += 1
        return self.send({"jsonrpc": "2.0", "id": self.msg_id, "method": method, "params": params or {}})

    def notify(self, method):
        return self.send({"jsonrpc": "2.0", "method": method})

    def tool(self, name, args=None):
        return self.call("tools/call", {"name": name, "arguments": args or {}})

    def close(self):
        try:
            self.p.stdin.close()
        except Exception:
            pass
        try:
            self.p.terminate()
        except Exception:
            pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    m = Mcp()
    try:
        if cmd == "state":
            for tool in ("get_game_state", "get_ui_state"):
                r = m.tool(tool)
                print(tool, "->", json.dumps(r.get("result"), ensure_ascii=False)[:1500])
        elif cmd == "key":
            print(json.dumps(m.tool("press_key", {"key": sys.argv[2]}), ensure_ascii=False)[:400])
            time.sleep(0.8)
            print(json.dumps(m.tool("get_ui_state").get("result"), ensure_ascii=False)[:800])
        elif cmd == "sequence":
            for tok in sys.argv[2].split():
                if tok == "wait":
                    time.sleep(1.2)
                    continue
                print("press", tok, "->", json.dumps(m.tool("press_key", {"key": tok}), ensure_ascii=False)[:160])
                time.sleep(0.9)
            print(json.dumps(m.tool("get_ui_state").get("result"), ensure_ascii=False)[:1200])
        elif cmd == "shot":
            r = m.tool("capture_screen")
            time.sleep(1.5)
            # capture 是异步返回的，再读一行
            line = m.p.stdout.readline()
            print("raw:", line[:120])
    finally:
        m.close()


if __name__ == "__main__":
    main()
