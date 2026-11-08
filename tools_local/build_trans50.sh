#!/usr/bin/env bash
# 编译 tools/trans50（kdef.grp -> script/event-cifa/*.cifa，顺便能转 talk）
set -e
export PATH=/e/msys64/ucrt64/bin:/e/msys64/usr/bin:$PATH
cd "$(dirname "$0")/../tools/trans50"

g++ -O2 -std=c++23 -pthread -DNDEBUG -o trans50.exe \
    main.cpp transk.cpp trans50.cpp ../../src/print_fix.cpp \
    ../../src/GrpIdxFile.cpp \
    ../../mlcc/filefunc.cpp ../../mlcc/strfunc.cpp ../../mlcc/PotConv.cpp ../../mlcc/SimpleCC.cpp \
    -I. -I../../src -I../../mlcc -I../../others -I../../include -liconv
echo "ok: tools/trans50/trans50.exe"
