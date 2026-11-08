"""把 kys.exe 依赖的 MSYS2 DLL（含传递依赖）拷到 dist/，做成自包含目录。"""
import os
import shutil
import subprocess

BIN = r"E:\msys64\ucrt64\bin"
EXE = r"E:\Games\kys-cpp\src\build\kys.exe"
OUT = r"E:\Games\kys-cpp\dist"

SYSTEM_PREFIX = (
    "api-ms-", "kernel32", "user32", "gdi32", "advapi32", "shell32", "ole32", "oleaut32",
    "winmm", "imm32", "version", "ws2_32", "setupapi", "cfgmgr32", "dwmapi", "uxtheme",
    "bcrypt", "crypt32", "shlwapi", "comdlg32", "comctl32", "ntdll", "msvcrt", "opengl32",
    "glu32", "dnsapi", "iphlpapi", "netapi32", "secur32", "wldap32", "dbghelp", "psapi",
    "powrprof", "rpcrt4", "hid", "mf", "mfplat", "mfuuid", "evr", "ksuser", "wininet",
    "normaliz", "wevtapi", "dwrite", "d3d", "usp10", "uiautomation",
)


def deps(path):
    objdump = os.path.join(BIN, "objdump.exe")
    out = subprocess.run([objdump, "-p", path], capture_output=True, text=True, errors="ignore").stdout
    return [line.split()[-1] for line in out.splitlines() if "DLL Name:" in line]


def main():
    os.makedirs(OUT, exist_ok=True)
    seen, queue, copied = set(), [EXE], []
    while queue:
        cur = queue.pop()
        for d in deps(cur):
            low = d.lower()
            if low in seen:
                continue
            seen.add(low)
            if any(low.startswith(p) for p in SYSTEM_PREFIX):
                continue
            src = os.path.join(BIN, d)
            if os.path.exists(src):
                dst = os.path.join(OUT, d)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    copied.append(d)
                queue.append(src)
            else:
                print("  未找到（可能是系统组件）:", d)
    shutil.copy2(EXE, os.path.join(OUT, "kys.exe"))
    print("dist 就绪：%d 个 DLL，共 %.1f MB" % (
        len(copied), sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) / 1048576))


if __name__ == "__main__":
    main()
