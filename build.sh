#!/usr/bin/env bash
# 一键重新编译 kys-cpp（MSYS2-UCRT64 + GCC16）
set -e
export MSYSTEM=UCRT64
export PATH=/e/msys64/ucrt64/bin:/e/msys64/usr/bin:$PATH
export CXX=g++

cd "$(dirname "$0")"

# 1) 依赖（首次运行）
if ! command -v g++ >/dev/null; then
  echo "请先安装 MSYS2 到 E:/msys64 并执行："
  echo "  pacman -S --needed mingw-w64-ucrt-x86_64-{gcc,cmake,ninja,pkgconf,sdl3,sdl3-image,sdl3-ttf,sdl3-mixer,sqlite3,yaml-cpp,libiconv,libpng}"
  exit 1
fi

# 2) 子模块与 glaze
[ -d mlcc/Cifa.cpp ] || git submodule update --init --recursive
[ -d glaze/include ] || git clone --depth 1 https://github.com/stephenberry/glaze.git glaze

# 2.1) cifa 子模块的 MinGW TLS 补丁（inline static thread_local 会 multiple definition）
if [ -f patches/0002-cifa-tls-fix.patch ]; then
  ( cd cifa
    if git apply --check ../patches/0002-cifa-tls-fix.patch 2>/dev/null; then
      git apply ../patches/0002-cifa-tls-fix.patch
      echo "已给 cifa 打 TLS 补丁"
    else
      echo "cifa 补丁已打过或无需再打"
    fi )
fi

# 3) 编译
cmake -S src -B src/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build src/build -j"$(nproc)"

# 4) 自包含目录
mkdir -p dist
cp src/build/kys.exe dist/
python3 tools_local/copy_dlls.py 2>/dev/null || true
echo "完成：src/build/kys.exe"

# 5) 可选：编译资源转换工具
#   ./tools_local/build_abc.sh        -> tools/abc/abc.exe（存档 16→32 位）
#   ./tools_local/build_trans50.sh    -> tools/trans50/trans50.exe（kdef → 事件脚本）
#   python3 tools_local/convert_dos_res.py   需要先把 DOS 原版数据放到 E:/Games/kys-dos-data
#   python3 tools_local/xmi2mid.py           音乐 XMI → MID
echo "构建完成。资源转换见 tools_local/ 与 编译说明.md"
