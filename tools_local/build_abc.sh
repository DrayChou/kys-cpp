#!/usr/bin/env bash
# 编译 tools/abc（存档 16→32 位转换 + SQLite 导出）
# 依赖：MSYS2-UCRT64 的 gcc / sqlite3 / libpng / libiconv
set -e
export PATH=/e/msys64/ucrt64/bin:/e/msys64/usr/bin:$PATH
cd "$(dirname "$0")/../tools/abc"

g++ -O2 -std=c++23 -pthread -DNDEBUG -o abc.exe \
    main.cpp abc.cpp png_offset.cpp zip_stub.cpp ../../src/print_fix.cpp \
    ../../src/GrpIdxFile.cpp \
    ../../mlcc/filefunc.cpp ../../mlcc/strfunc.cpp ../../mlcc/PotConv.cpp \
    ../../mlcc/SimpleCC.cpp ../../mlcc/SQLite3Wrapper.cpp ../../mlcc/ZipFile2.cpp \
    -I. -I../../src -I../../mlcc -I../../others -I../../include \
    -lsqlite3 -lpng -liconv -lz
echo "ok: tools/abc/abc.exe"
