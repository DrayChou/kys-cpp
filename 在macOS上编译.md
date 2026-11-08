# 在 macOS 上编译《金庸群侠传》C++ 复刻版（KYS-CPP）

> 适用于仓库 <https://github.com/DrayChou/kys-cpp>（= 上游 + 本机移植补丁）
> Windows 侧的完整记录见 `编译说明.md`，这篇只讲 Mac 上要注意的差异。

---

## 一、一句话版

```bash
# 1. 依赖（Apple Silicon 与 Intel 都适用）
brew install cmake ninja sdl3 sdl3_image sdl3_ttf sdl3_mixer sqlite yaml-cpp libiconv libpng

# 2. 编译
git clone https://github.com/DrayChou/kys-cpp.git && cd kys-cpp
./build-macos.sh

# 3. 资源（最省事：从 Windows 那台整包拷过来）
scp -r win-pc:/E/Games/kys-cpp/game ./game

# 4. 运行
./build-mac/kys ./game
```

---

## 二、环境要求

| 项 | 要求 | 说明 |
|---|---|---|
| macOS | 13 以上 | Apple Silicon / Intel 都行 |
| Xcode CLT | `xcode-select --install` | 提供 SDK 与 clang |
| **编译器** | **Xcode 16.3+（libc++ 19）** 或 `brew install gcc` | 关键：代码里用了 `std::print`，libc++ 要 19 才有 |
| Homebrew | 任意 | 依赖都走 brew |
| 磁盘 | ≥ 2 GB | 源码 + 构建 + 资源（game 约 71 MB） |

**关于编译器**：`src/Engine.cpp`、`src/Engine.h`、`cifa/Cifa.cpp` 用了 `std::print`（C++23）。

- Xcode 16.3+ 自带 libc++ 19，`<print>` 可用 → 直接用默认 clang++
- 老一点的 Xcode（libc++ 18 及以下）编译会报 `'print' is not a member of 'std'` → 换成 GCC：

```bash
brew install gcc
CXX=g++-14 ./build-macos.sh
```

---

## 三、和 Windows 版的差异（重点，少踩坑）

| 项 | Windows（MSYS2/MinGW） | macOS | 你要做什么 |
|---|---|---|---|
| `src/print_fix.cpp` | **必须**（MinGW 的 libstdc++ 缺 `__open_terminal`/`__write_to_terminal`） | **不需要** | 已经用 `#if defined(_WIN32)` 包起来了，Mac 上编译成空文件，什么都不用改 |
| iconv | 我在 CMake 里加了 `if (MINGW)` 分支 | CMake 本来就有 `if (APPLE)` 分支 | `brew install libiconv` 即可 |
| 运行库打包 | `tools_local/copy_dlls.py` 拷 21 个 DLL | **不需要** | brew 装的 dylib 自带 rpath，直接跑 |
| 构建脚本 | `build.sh`（写死 `/e/msys64` 路径） | 用 `build-macos.sh` | 别在 Mac 上跑 build.sh |
| `<cstdint>` / `<cmath>` 补齐 | 必须 | **同样需要**（这些改动已经在仓库里，跨平台有效） | 无 |
| cifa 的 TLS 补丁 | 必须（否则 multiple definition） | 建议也打（同样是 ODR 问题，clang 下可能不报错，但打了更稳） | `build-macos.sh` 会自动打 |
| 资源转换工具 | `abc.exe` / `trans50.exe` | 需要重新编译成 Mach-O | 见第五节 |

---

## 四、逐步骤

### 4.1 装依赖

```bash
xcode-select --install
brew install cmake ninja sdl3 sdl3_image sdl3_ttf sdl3_mixer sqlite yaml-cpp libiconv libpng
```

> `sdl3*` 是 SDL3 系列（不是 SDL2）。上游现在用的是 SDL3 3.x + ttf 3.x + image 3.x + mixer 3.x。

### 4.2 取代码

```bash
git clone https://github.com/DrayChou/kys-cpp.git
cd kys-cpp
git submodule update --init --recursive      # mlcc / cifa
git clone --depth 1 https://github.com/stephenberry/glaze.git glaze
```

**注意 glaze**：`src/CMakeLists.txt` 里写死了 `../glaze/include`，但 glaze 不是本仓库的子模块，必须自己 clone 到仓库根目录下、且目录名就叫 `glaze`。

### 4.3 编译

```bash
./build-macos.sh
```

脚本做的事（想手动执行的话）：

```bash
BREW_PREFIX="$(brew --prefix)"
cmake -S src -B build-mac -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$BREW_PREFIX"
cmake --build build-mac -j"$(sysctl -n hw.ncpu)"
# 产物：build-mac/kys
```

Intel Mac 的 brew 前缀是 `/usr/local`，脚本里用 `brew --prefix` 自动处理，不用改。

---

## 五、资源目录（game/）

### 方案 A：从 Windows 那台直接拷（推荐）

```bash
# 在 Mac 上
scp -r 用户名@win-ip:E:/Games/kys-cpp/game ./game     # 或者用 U 盘、AirDrop、网盘
```

拷完检查这几个子目录都在：

```
game/
├─ cc/        繁简词表（2 个 txt）
├─ config/    kysmod.ini（简体/窗口/音量/标题）
├─ font/      chinese.ttf   ← 中文字体，必须
├─ list/      levelup.txt、leave.txt
├─ music/     mid.sf2 + 1..24.mid
├─ resource/  贴图组 + kdef + talkutf8.txt + *.002
├─ save/      0~3.db + allsin.grp + alldef.grp
├─ script/    event-cifa/*.cifa（994 个，剧情核心）
└─ sound/     音效 wav
```

### 方案 B：在 Mac 上现场转换

需要先把 DOS 原版《金庸群侠传》数据放到某个目录（Windows 上那份在 `E:\Games\kys-dos-data`）。

```bash
export DOS_DATA=~/kys-dos-data        # 里面是 KDEF.GRP / TALK.GRP / FIGHT*.GRP / *.002 ...

# 1) 贴图 + 对话（纯 Python，跨平台）
python3 tools_local/convert_dos_res.py     # 脚本里 DOS/JYOL/OUT 三个路径按需改

# 2) 存档 16→32 位（需要编译 abc）
brew install libzip                        # macOS 上可以直接用真正的 ZipFile.cpp
./tools_local/build_converters_macos.sh

tools/abc/abc --save -p ~/saveconv/        # 生成 0~3.db
cp ~/saveconv/*.db game/save/
cp $DOS_DATA/ALLSIN.GRP game/save/allsin.grp
cp $DOS_DATA/ALLDEF.GRP game/save/alldef.grp

# 3) 事件脚本（994 个 .cifa，没有它剧情全哑）
tools/trans50/trans50 --kdef -i game/resource -o game -t game/resource/talkutf8.txt

# 4) 战斗帧数表
cp $DOS_DATA/RANGER.* game/resource/fight/
tools/abc/abc --save -p game/resource/fight/
rm game/resource/fight/ranger.* game/resource/fight/0.db

# 5) 音乐（DOS 的 XMIDI -> 标准 MIDI）
python3 tools_local/xmi2mid.py
```

> 第 1、5 步的脚本里路径是写死的（`E:\Games\...`），Mac 上跑之前把 `DOS` / `JYOL` / `OUT` 三个变量改成你的路径。

### 5.1 大小写敏感卷的坑

DOS 原始数据里的文件名是大写的（`KDEF.GRP`、`EARTH.002`），而程序里全是小写。

- 默认的 APFS 卷**大小写不敏感** → 没问题
- 如果你把游戏放在**大小写敏感**的卷/分区上 → 必须全转小写：

```bash
find game -type f | while read f; do
  n="$(dirname "$f")/$(basename "$f" | tr 'A-Z' 'a-z')"
  [ "$f" != "$n" ] && mv "$f" "$n"
done
```

---

## 六、运行

```bash
./build-mac/kys ./game
```

- 第一个参数就是 `game` 目录的路径，给错了会黑屏并提示 `Game path is ...`
- 窗口标题应当在 `config/kysmod.ini` 里配（现在是「金庸群侠传（C++ 复刻版）」）
- 首次运行如果把二进制从网上下载下来，macOS 可能提示"无法验证开发者"：

```bash
xattr -dr com.apple.quarantine build-mac/kys
```

---

## 七、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `'print' is not a member of 'std'` | libc++ 版本太旧 | `brew install gcc && CXX=g++-14 ./build-macos.sh` |
| `SDL3 not found` | brew 前缀没找到 | 确认 `-DCMAKE_PREFIX_PATH="$(brew --prefix)"` |
| 链接报 `__open_terminal` 重复定义 | 你把 `print_fix.cpp` 的 `#if defined(_WIN32)` 删了 | 恢复那行宏，Mac 上这段必须不参与编译 |
| 运行黑屏、控制台刷 `Load texture group ... 0 textures` | `game/` 路径给错，或者资源没拷全 | 用绝对路径试：`./build-mac/kys "$(pwd)/game"` |
| 有画面但没剧情、NPC 不说话 | `game/script/event-cifa/` 是空的 | 补第 5 节第 3 步 |
| 中文全是方块 | `game/font/chinese.ttf` 缺失或不是中文字体 | 从 Windows 拷一份，或换任意 CJK TTF |
| 没有音乐 | `music/*.mid` 或 `music/mid.sf2` 缺失 | 补第 5 节第 5 步；`brew install fluid-synth` |
| 存档存不上 | 默认写 `game/save/` | 确认该目录可写 |

---

## 八、编译完应该看到什么（自检清单）

1. `build-mac/kys` 存在，大小 4~6 MB
2. 启动后出现标题画面（金庸群侠传 Logo + 三个简体按钮：新游戏 / 读取进度 / 离开游戏）
3. 新游戏 → 输入姓名 → 随机属性界面（"升级 100"）→ 进入「主角的家」
4. 开场对白正常滚动，**字不叠、不黑**
5. 右键或 ESC → 顶部出现「状态 / 物品 / 系统」，点「系统」能看见「读取进度 / 保存进度 / 游戏配置 / 离开游戏」

这 5 条都对，就说明 Mac 版和 Windows 版行为一致了。
