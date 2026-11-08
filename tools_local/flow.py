"""kys-cpp MCP 驱动：一次进程内跑完整流程（菜单->新游戏->读状态->截图）。

用法:
  python flow.py "confirm,wait,confirm,wait"      # 逗号分隔的步骤
  步骤: up/down/left/right/confirm/cancel/wait/shot:<文件名>/state
"""
import json
import os
import subprocess
import sys
import time

EXE = r"E:\Games\kys-cpp\dist\kys.exe"
GAME = r"E:\Games\kys-cpp\game"
WORKDIR = r"E:\Games\kys-cpp"
SHOT = r"E:\Games\_tools\shotwin.ps1"


class Mcp:
    def __init__(self):
        env = dict(os.environ)
        env["PATH"] = r"E:\Games\kys-cpp\dist;" + env.get("PATH", "")
        self.p = subprocess.Popen([EXE, GAME, "--mcp-stdio"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=open(r"E:\Games\kys-cpp\game_err.txt", "wb"),
                                  cwd=WORKDIR, env=env, bufsize=1, text=True,
                                  encoding="utf-8", errors="replace")
        self.n = 0
        self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "driver", "version": "1"}})
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def read_until(self, want, timeout=20):
        t0 = time.time()
        while time.time() - t0 < timeout:
            line = self.p.stdout.readline()
            if not line:
                return None
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if msg.get("id") == want:
                return msg
        return None

    def call(self, method, params=None):
        self.n += 1
        self.send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params or {}})
        return self.read_until(self.n)

    def tool(self, name, args=None):
        r = self.call("tools/call", {"name": name, "arguments": args or {}})
        if not r:
            return None
        try:
            return json.loads(r["result"]["content"][0]["text"])
        except Exception:
            return r

    def alive(self):
        return self.p.poll() is None


def main():
    steps = sys.argv[1].split(",") if len(sys.argv) > 1 else ["state"]
    m = Mcp()
    try:
        for step in steps:
            step = step.strip()
            if not step:
                continue
            if step == "wait":
                time.sleep(1.5)
                continue
            if step == "state":
                gs = m.tool("get_game_state")
                ui = m.tool("get_ui_state")
                print("STATE", json.dumps({"game": gs, "ui": ui}, ensure_ascii=False)[:900])
                continue
            if step.startswith("cl:"):
                xy = step[3:].replace(";", ",")
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                "-File", r"E:\Games\_tools\wnclick.ps1", "-Title", "*金庸*",
                                "-Actions", "w:300;c:%s;w:1200" % xy], capture_output=True)
                print("CLICK", xy)
                continue
            if step.startswith("rc:"):
                xy = step[3:].replace(";", ",")
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                "-File", r"E:\Games\_tools\wnclick.ps1", "-Title", "*金庸*",
                                "-Actions", "w:400;r:%s;w:1200" % xy], capture_output=True)
                print("RIGHTCLICK", xy)
                continue
            if step.startswith("shot:"):
                out = step[5:]
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                "-File", SHOT, "-TitleLike", "*金庸*", "-Out", out],
                               capture_output=True)
                print("SHOT", out)
                continue
            r = m.tool("press_key", {"key": step})
            print("KEY", step, "->", json.dumps(r, ensure_ascii=False)[:200])
            time.sleep(1.2)
            if not m.alive():
                print("!! 进程已退出, returncode =", m.p.returncode)
                break
        # 保持窗口 20 秒，方便外部截图
        for _ in range(20):
            if not m.alive():
                break
            time.sleep(1)
    finally:
        try:
            m.p.stdin.close()
        except Exception:
            pass
        try:
            m.p.wait(timeout=5)
        except Exception:
            m.p.terminate()


if __name__ == "__main__":
    main()
