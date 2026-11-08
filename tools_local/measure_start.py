import subprocess, time, os, sys
exe = r'E:\Games\kys-cpp\dist\kys.exe'
game = r'E:\Games\kys-cpp\game'
log = r'E:\Games\_sync\start.log'
if os.path.exists(log): os.remove(log)
t0 = time.time()
with open(log,'w',encoding='utf-8',errors='replace') as f:
    p = subprocess.Popen([exe, game], cwd=r'E:\Games\kys-cpp', stdout=f, stderr=subprocess.STDOUT)
    ok=None
    for _ in range(300):
        time.sleep(0.1)
        try: txt=open(log,encoding='utf-8',errors='replace').read()
        except Exception: txt=''
        if 'title,' in txt:
            ok=time.time()-t0; break
    p.terminate(); p.wait(timeout=10)
print("到 title 就绪: %.2f 秒" % ok if ok else "超时")
