#!/usr/bin/env bash
# macOS 一键编译（Apple Silicon / Intel 都适用）
#
# 用法：
#   ./build-macos.sh              # 用默认编译器（推荐 Xcode 16.3+ 的 clang++）
#   CXX=g++-14 ./build-macos.sh   # 用 Homebrew 的 GCC（libc++ 太旧时用这个）
#
# 依赖：
#   xcode-select --install
#   brew install cmake ninja sdl3 sdl3_image sdl3_ttf sdl3_mixer sqlite yaml-cpp libiconv libpng
set -e
cd "$(dirname "$0")"

# ---- 1. 依赖自检 ----
missing=()
for pkg in sdl3 sdl3_image sdl3_ttf sdl3_mixer sqlite yaml-cpp; do
  brew list --versions "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "缺少依赖：${missing[*]}"
  echo "请先执行： brew install ${missing[*]}"
  exit 1
fi

# ---- 2. 子模块 + glaze ----
[ -f mlcc/Cifa.cpp ] || git submodule update --init --recursive
[ -d glaze/include ] || git clone --depth 1 https://github.com/stephenberry/glaze.git glaze

# ---- 3. cifa 的 TLS 补丁（可移植，建议打；已打过会跳过）----
if [ -f patches/0002-cifa-tls-fix.patch ]; then
  ( cd cifa
    if git apply --check ../patches/0002-cifa-tls-fix.patch 2>/dev/null; then
      git apply ../patches/0002-cifa-tls-fix.patch
      echo "已给 cifa 打 TLS 补丁"
    else
      echo "cifa 补丁已打过或无需再打"
    fi )
fi

# ---- 4. 编译 ----
# Homebrew 前缀：Apple Silicon 是 /opt/homebrew，Intel 是 /usr/local
BREW_PREFIX="$(brew --prefix)"
BUILD_DIR="build-mac"

cmake -S src -B "$BUILD_DIR" -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_PREFIX_PATH="$BREW_PREFIX"
cmake --build "$BUILD_DIR" -j"$(sysctl -n hw.ncpu)"

echo
echo "编译完成：$(pwd)/$BUILD_DIR/kys"
echo "运行： ./$BUILD_DIR/kys \"$(pwd)/game\""
echo
echo "如果没有 game 目录，把 Windows 那台的 game/ 整个拷过来，"
echo "或者在 Mac 上按 在macOS上编译.md 的第 4 节现场转换资源。"
