#!/usr/bin/env bash
# 在 macOS 上编译资源转换工具：abc（存档 16→32 位 + SQLite）和 trans50（kdef → 事件脚本）
#
# 依赖：brew install cmake libpng libiconv libzip  （cc 用系统 clang++ 或 CXX=g++-14）
set -e
cd "$(dirname "$0")/.."          # 仓库根目录

CXX="${CXX:-c++}"
BREW_PREFIX="$(brew --prefix)"
INC="-I$BREW_PREFIX/include"
LIB="-L$BREW_PREFIX/lib"
JOBS="$(sysctl -n hw.ncpu)"

# macOS 上 zlib 不带 zip.h，可以直接用真正的 ZipFile.cpp；
# 没有 libzip 时才退回 zip_stub.cpp。
ZIP_SRC=""
if [ -f "$BREW_PREFIX/include/zip.h" ] && [ -f "$BREW_PREFIX/lib/libzip.dylib" -o -f "$BREW_PREFIX/lib/libzip.a" ]; then
  ZIP_SRC="mlcc/ZipFile.cpp"; ZIP_LIB="-lzip"
  echo "使用 libzip"
else
  ZIP_SRC="tools/abc/zip_stub.cpp"; ZIP_LIB=""
  echo "未找到 libzip，使用 zip_stub.cpp（--trans-indexka 不可用）"
fi

echo "== 编译 abc =="
( cd tools/abc && "$CXX" -O2 -std=c++23 -DNDEBUG -o abc \
    main.cpp abc.cpp png_offset.cpp ../../$ZIP_SRC ../../src/print_fix.cpp \
    ../../src/GrpIdxFile.cpp \
    ../../mlcc/filefunc.cpp ../../mlcc/strfunc.cpp ../../mlcc/PotConv.cpp \
    ../../mlcc/SimpleCC.cpp ../../mlcc/SQLite3Wrapper.cpp ../../mlcc/ZipFile2.cpp \
    -I. -I../../src -I../../mlcc -I../../others -I../../include $INC $LIB \
    -lsqlite3 -lpng -liconv -lz $ZIP_LIB )

echo "== 编译 trans50 =="
( cd tools/trans50 && "$CXX" -O2 -std=c++23 -DNDEBUG -o trans50 \
    main.cpp transk.cpp trans50.cpp ../../src/print_fix.cpp \
    ../../src/GrpIdxFile.cpp \
    ../../mlcc/filefunc.cpp ../../mlcc/strfunc.cpp ../../mlcc/PotConv.cpp ../../mlcc/SimpleCC.cpp \
    -I. -I../../src -I../../mlcc -I../../others -I../../include $INC $LIB \
    -liconv )

echo
echo "完成："
echo "  tools/abc/abc"
echo "  tools/trans50/trans50"
