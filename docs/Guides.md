# Hướng dẫn Build & Debug Bamboo Engine

> Tài liệu dành cho lập trình viên mới tham gia dự án. Engine là fork của Godot (4.8-dev), build bằng **SCons**.
> Tài liệu kiến trúc: [architecture.md](architecture.md) · [ENGINE_ANALYSIS.md](ENGINE_ANALYSIS.md) · [Render_Architecture.md](Render_Architecture.md) · [Camera_Architecture.md](Camera_Architecture.md) · [Navigation_Architecture.md](Navigation_Architecture.md) · [Display_Architecture.md](Display_Architecture.md)

---

## Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Chuẩn bị môi trường](#2-chuẩn-bị-môi-trường)
3. [Build editor lần đầu](#3-build-editor-lần-đầu)
4. [Các cờ build quan trọng](#4-các-cờ-build-quan-trọng)
5. [Chạy engine](#5-chạy-engine)
6. [Debug C++ bằng IDE / debugger](#6-debug-c-bằng-ide--debugger)
7. [Công cụ debug runtime](#7-công-cụ-debug-runtime)
8. [Unit test](#8-unit-test)
9. [Build export template (bản chạy game)](#9-build-export-template-bản-chạy-game)
10. [Code style & trước khi commit](#10-code-style--trước-khi-commit)
11. [Xử lý sự cố thường gặp](#11-xử-lý-sự-cố-thường-gặp)
12. [Quy ước riêng của Bamboo](#12-quy-ước-riêng-của-bamboo)

---

## 1. Yêu cầu hệ thống

Yêu cầu chung (kiểm tra trong `SConstruct:4-5`):

| Công cụ | Phiên bản tối thiểu |
| :--- | :--- |
| Python | 3.9 |
| SCons | 4.4 |
| C++ compiler | hỗ trợ C++17 |
| RAM | ≥ 8 GB (khuyến nghị 16 GB khi build song song) |
| Ổ đĩa | ~15–25 GB cho source + object file của nhiều cấu hình |

Theo nền tảng:

| Nền tảng | Compiler / SDK | Ghi chú |
| :--- | :--- | :--- |
| **macOS** | Xcode (Apple Clang) + Command Line Tools | Metal bật mặc định trên arm64. Vulkan (MoltenVK) cần Vulkan SDK — nếu không cài thì build với `vulkan=no` |
| **Windows** | Visual Studio 2022 (workload "Desktop development with C++") hoặc MinGW-w64 / LLVM-MinGW | D3D12 cần chạy `install_d3d12_sdk_windows.py` và build với `d3d12=yes` |
| **Linux** | GCC hoặc Clang, `pkg-config`, header X11/Wayland/ALSA/PulseAudio/udev | Xem lệnh cài gói bên dưới |
| **Android** | Android SDK + NDK, JDK 17 | Xem tài liệu Godot "Compiling for Android" |
| **Web** | Emscripten SDK | Xem tài liệu Godot "Compiling for the Web" |

Gói cần cài trên Ubuntu/Debian:

```bash
sudo apt install build-essential scons pkg-config libx11-dev libxcursor-dev libxinerama-dev libgl1-mesa-dev libglu1-mesa-dev libasound2-dev libpulse-dev libudev-dev libxi-dev libxrandr-dev libwayland-dev
```

---

## 2. Chuẩn bị môi trường

### 2.1 Lấy source

```bash
git clone <URL-repo-bamboo> bamboo
```

```bash
cd bamboo
```

### 2.2 Cài SCons

```bash
python3 -m pip install --upgrade scons
```

Kiểm tra:

```bash
scons --version
```

### 2.3 Cài dependency tùy chọn (khuyến nghị)

Các thư viện này **không bắt buộc** — nếu thiếu, SCons in cảnh báo và tự tắt tính năng tương ứng (trừ Vulkan trên macOS, xem §11). Các script nằm trong `misc/scripts/`:

| Script | Dùng cho | Nền tảng |
| :--- | :--- | :--- |
| `install_accesskit.py` | Screen reader (AccessKit) | Windows, macOS, Linux |
| `install_angle.py` | ANGLE (OpenGL ES trên D3D11/Metal) | Windows, macOS |
| `install_vulkan_sdk_macos.sh` | Vulkan SDK / MoltenVK | macOS |
| `install_d3d12_sdk_windows.py` | Agility SDK, Mesa NIR, PIX cho D3D12 | Windows |
| `install_swappy_android.py` | Swappy frame pacing | Android |
| `install_perfetto.py` | Profiler Perfetto | Tất cả |

Ví dụ trên macOS:

```bash
python3 misc/scripts/install_accesskit.py
```

```bash
python3 misc/scripts/install_angle.py
```

```bash
sh misc/scripts/install_vulkan_sdk_macos.sh
```

---

## 3. Build editor lần đầu

Bản dùng hằng ngày cho dev là **editor + dev_build + debug symbols**: có đầy đủ assert, code `DEV_ENABLED`, và debug được bằng debugger.

### macOS (Apple Silicon)

```bash
scons platform=macos arch=arm64 target=editor dev_build=yes debug_symbols=yes compiledb=yes
```

Nếu chưa cài Vulkan SDK:

```bash
scons platform=macos arch=arm64 target=editor dev_build=yes debug_symbols=yes compiledb=yes vulkan=no
```

### Windows (MSVC, chạy trong "x64 Native Tools Command Prompt for VS 2022")

```bash
scons platform=windows target=editor dev_build=yes debug_symbols=yes vsproj=yes
```

### Linux

```bash
scons platform=linuxbsd target=editor dev_build=yes debug_symbols=yes compiledb=yes linker=mold
```

(`linker=mold` hoặc `linker=lld` giúp link nhanh hơn nhiều; bỏ đi nếu chưa cài.)

### Kết quả

Binary nằm trong `bin/`, tên theo mẫu:

```
bamboo.<platform>.<target>[.dev][.double].<arch>[.llvm][.console][.exe]
```

| Lệnh | File sinh ra |
| :--- | :--- |
| macOS dev editor | `bin/bamboo.macos.editor.dev.arm64` |
| Windows dev editor (MSVC) | `bin/bamboo.windows.editor.dev.x86_64.exe` + `.console.exe` |
| Windows dev editor (LLVM-MinGW) | `bin/bamboo.windows.editor.dev.x86_64.llvm.exe` |
| Linux dev editor | `bin/bamboo.linuxbsd.editor.dev.x86_64` |

> **Mẹo:** SCons tự dùng số luồng = số CPU. Lần build đầu mất 15–60 phút tùy máy; các lần sau chỉ build lại phần thay đổi. Trên Windows, dùng bản `.console.exe` để thấy log trong terminal.

---

## 4. Các cờ build quan trọng

Xem đầy đủ bằng `scons --help` (định nghĩa trong `SConstruct:161-381` và `platform/<name>/detect.py`).

### 4.1 Mục tiêu & tối ưu

| Cờ | Giá trị | Ý nghĩa |
| :--- | :--- | :--- |
| `platform` (`p`) | `macos`, `windows`, `linuxbsd`, `android`, `ios`, `visionos`, `web` | Nền tảng đích |
| `target` | `editor` · `template_debug` · `template_release` | Editor / bản chạy game có debug / bản phát hành |
| `arch` | `auto`, `x86_64`, `arm64`, … | Kiến trúc CPU |
| `dev_build` | `yes/no` | Bật `DEV_ENABLED`, assert dev, tắt tối ưu mặc định — **dùng khi phát triển engine** |
| `debug_symbols` | `yes/no` | Thêm symbol để debugger hiển thị code |
| `separate_debug_symbols` | `yes/no` | Tách symbol ra file riêng |
| `optimize` | `auto`, `none`, `debug`, `speed`, `speed_trace`, `size`, `size_extra` | Mức tối ưu |
| `production` | `yes/no` | Preset cho bản phát hành (`lto=auto`, static C++, không symbol) |
| `dev_mode` | `yes/no` | Alias: `verbose=yes warnings=extra werror=yes tests=yes strict_checks=yes` (CI dùng) |

### 4.2 Tăng tốc build

| Cờ | Ý nghĩa |
| :--- | :--- |
| `scu_build=yes` | Single compilation unit — build sạch nhanh hơn đáng kể, tốn RAM hơn (`scu_limit` để giới hạn) |
| `ninja=yes` | Sinh `build.ninja`, rebuild nhanh hơn |
| `cache_path=<dir>` + `cache_limit=<GiB>` | Cache object file của SCons giữa các nhánh |
| `cpp_compiler_launcher=ccache` / `c_compiler_launcher=ccache` | Dùng ccache |
| `fast_unsafe=yes` | Bỏ một số kiểm tra của SCons để rebuild nhanh (chỉ dùng local) |
| `linker=mold` / `linker=lld` (Linux) | Linker nhanh |

### 4.3 Công cụ hỗ trợ IDE

| Cờ | Ý nghĩa |
| :--- | :--- |
| `compiledb=yes` | Sinh `compile_commands.json` cho clangd / VS Code / CLion (repo đã có `.clangd`) |
| `vsproj=yes` | Sinh solution Visual Studio (`godot.sln`) |

### 4.4 Debug nâng cao

| Cờ | Ý nghĩa |
| :--- | :--- |
| `use_asan=yes` | AddressSanitizer — bắt lỗi bộ nhớ (out-of-bounds, use-after-free) |
| `use_ubsan=yes` | UndefinedBehaviorSanitizer |
| `use_tsan=yes` | ThreadSanitizer — bắt data race (không dùng chung với ASAN) |
| `strict_checks=yes` | Thêm kiểm tra chặt (`STRICT_CHECKS`) |
| `tests=yes` | Build kèm unit test (doctest) |
| `profiler=tracy\|perfetto\|instruments` + `profiler_path=…` | Tích hợp profiler CPU |

### 4.5 Lưu cấu hình build cá nhân

Tạo file `custom.py` ở thư mục gốc (SCons tự đọc, file này **không commit**):

```python
platform = "macos"
arch = "arm64"
target = "editor"
dev_build = "yes"
debug_symbols = "yes"
compiledb = "yes"
vulkan = "no"
```

Sau đó chỉ cần chạy:

```bash
scons
```

Hoặc dùng profile dùng chung cho team (thư mục `profiles/` chưa có trong repo — tạo khi team thống nhất cấu hình): `scons profile=profiles/bamboo_dev.py`.

---

## 5. Chạy engine

### 5.1 Mở Project Manager / Editor

```bash
bin/bamboo.macos.editor.dev.arm64
```

Mở thẳng editor cho một project:

```bash
bin/bamboo.macos.editor.dev.arm64 --path /path/to/game_project --editor
```

Chạy game (không mở editor):

```bash
bin/bamboo.macos.editor.dev.arm64 --path /path/to/game_project
```

Chạy một scene cụ thể:

```bash
bin/bamboo.macos.editor.dev.arm64 --path /path/to/game_project res://scenes/test_level.tscn
```

> Mẹo: tạo một project nhỏ `sandbox/` (ngoài repo hoặc trong `.gitignore`) chứa scene thử nghiệm để chạy nhanh khi debug.

### 5.2 Cờ dòng lệnh hữu ích khi debug

Xem đầy đủ: `bin/bamboo.<...> --help` (định nghĩa trong `main/main.cpp`).

| Cờ | Tác dụng |
| :--- | :--- |
| `-v`, `--verbose` | In log chi tiết (load resource, driver, shader…) |
| `-d`, `--debug` | Bật debugger dòng lệnh cục bộ cho script |
| `--log-file <path>` | Ghi log ra file |
| `--headless` | Không cửa sổ, không âm thanh (CI, server) |
| `--quit` | Thoát sau frame đầu tiên (kiểm tra khởi động) |
| `--rendering-driver vulkan\|metal\|d3d12\|opengl3` | Ép GPU API |
| `--rendering-method forward_plus\|mobile\|gl_compatibility` | Ép renderer |
| `--display-driver <name>` | Ép DisplayServer (`x11`, `wayland`, `headless`, …) |
| `--gpu-validation` | Bật validation layer của graphics API |
| `--gpu-abort` | Dừng ngay khi có lỗi graphics API (dễ bắt điểm lỗi trong debugger) |
| `--gpu-profile` | In các tác vụ GPU tốn thời gian nhất |
| `--print-fps` | In FPS ra stdout |
| `--max-fps <n>` / `--frame-delay <ms>` / `--time-scale <x>` | Điều khiển nhịp chạy |
| `--single-threaded-scene` | Chạy SceneTree đơn luồng (loại trừ lỗi đa luồng) |
| `--disable-crash-handler` | Tắt crash handler để debugger bắt crash trực tiếp |
| `--debug-collisions` / `--debug-paths` / `--debug-navigation` / `--debug-avoidance` | Vẽ collision, path, navmesh, avoidance |
| `--debug-canvas-item-redraw` | Hiển thị vùng canvas item bị vẽ lại |
| `--debug-stringnames` | In thống kê cấp phát `StringName` khi thoát |
| `--profiling` | Bật profiling trong script debugger |
| `--benchmark` | Đo thời gian chạy |
| `--dump-extension-api` | Xuất `extension_api.json` cho GDExtension |

---

## 6. Debug C++ bằng IDE / debugger

Luôn debug trên bản build có `dev_build=yes debug_symbols=yes`. Khi muốn debugger bắt crash trực tiếp, thêm `--disable-crash-handler`.

### 6.1 VS Code (mọi nền tảng)

1. Cài extension: **clangd** (code navigation dùng `compile_commands.json`) và **CodeLLDB** (macOS/Linux) hoặc **C/C++** (Windows, kiểu `cppvsdbg`).
2. Build với `compiledb=yes`.
3. Tạo `.vscode/tasks.json` (thư mục `.vscode/` đã nằm trong `.gitignore`):

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "build-editor-dev",
      "type": "shell",
      "command": "scons",
      "args": ["target=editor", "dev_build=yes", "debug_symbols=yes", "compiledb=yes"],
      "group": { "kind": "build", "isDefault": true },
      "problemMatcher": "$gcc"
    }
  ]
}
```

4. Tạo `.vscode/launch.json` (macOS/Linux với CodeLLDB):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Bamboo: Project Manager",
      "type": "lldb",
      "request": "launch",
      "program": "${workspaceFolder}/bin/bamboo.macos.editor.dev.arm64",
      "args": ["--disable-crash-handler"],
      "cwd": "${workspaceFolder}",
      "preLaunchTask": "build-editor-dev"
    },
    {
      "name": "Bamboo: Editor (sandbox project)",
      "type": "lldb",
      "request": "launch",
      "program": "${workspaceFolder}/bin/bamboo.macos.editor.dev.arm64",
      "args": ["--path", "${workspaceFolder}/../sandbox", "--editor", "--verbose", "--disable-crash-handler"],
      "cwd": "${workspaceFolder}"
    },
    {
      "name": "Bamboo: Run game (sandbox project)",
      "type": "lldb",
      "request": "launch",
      "program": "${workspaceFolder}/bin/bamboo.macos.editor.dev.arm64",
      "args": ["--path", "${workspaceFolder}/../sandbox", "--verbose", "--disable-crash-handler"],
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

Trên Windows thay `"type": "cppvsdbg"` và `program` bằng `bin/bamboo.windows.editor.dev.x86_64.exe`; trên Linux đổi tên binary thành `bamboo.linuxbsd.editor.dev.x86_64`.

> **Lưu ý quan trọng:** Khi bấm **Run** trong editor, Godot **khởi chạy một process con** để chạy game. Debugger gắn vào editor sẽ **không** dừng ở breakpoint trong code game. Để debug code chạy trong game: dùng cấu hình "Run game" ở trên (chạy thẳng project), hoặc **attach** vào process con sau khi bấm Run.

### 6.2 Xcode / LLDB (macOS)

Dùng LLDB trực tiếp:

```bash
lldb -- bin/bamboo.macos.editor.dev.arm64 --path ../sandbox --disable-crash-handler
```

Trong LLDB: `b Node::add_child`, `run`, `bt`, `frame variable`, `continue`.

Dùng Xcode: **Debug → Attach to Process** (chọn `bamboo.macos.editor.dev.arm64`), hoặc tạo scheme "External Build System" trỏ tới binary. Xcode còn có **Metal Frame Capture** để debug GPU (xem §7.2).

### 6.3 Visual Studio (Windows)

1. Build với `vsproj=yes` → mở `godot.sln`.
2. Chọn cấu hình tương ứng (editor / dev), đặt **Command Arguments** trong Project Properties → Debugging (ví dụ `--path C:\dev\sandbox --disable-crash-handler`).
3. Nhấn F5. Visual Studio dùng lại lệnh SCons để build.
4. Debug process game con: **Debug → Attach to Process** hoặc cài extension *Microsoft Child Process Debugging Power Tool* để tự attach.

### 6.4 GDB (Linux)

```bash
gdb --args bin/bamboo.linuxbsd.editor.dev.x86_64 --path ../sandbox --disable-crash-handler
```

### 6.5 Breakpoint hữu ích để bắt đầu

| Muốn hiểu | Đặt breakpoint tại |
| :--- | :--- |
| Thứ tự khởi tạo engine | `Main::setup` (`main/main.cpp:974`), `Main::setup2`, `Main::start` |
| Một frame | `Main::iteration` (`main/main.cpp:4917`) |
| Vẽ frame | `RenderingServerDefault::_draw` (`servers/rendering/rendering_server_default.cpp:76`) |
| Input | `Window::_window_input` (`scene/main/window.cpp:2013`), `Viewport::push_input` |
| Node vào cây | `Node::_propagate_enter_tree`, `Node::_propagate_ready` |
| Load resource | `ResourceLoader::load` |
| Lỗi engine in ra console | `_err_print_error` (`core/error/error_macros.cpp`) — dừng tại **mọi** `ERR_*` |

---

## 7. Công cụ debug runtime

### 7.1 Debugger trong editor (script & engine)

Khi chạy game từ editor, tab **Debugger** cung cấp:

- **Stack trace / Errors**: lỗi và cảnh báo kèm vị trí.
- **Profiler**: thời gian từng hàm script và các nhóm engine (bật `--profiling` khi chạy CLI).
- **Visual Profiler**: thời gian CPU/GPU theo từng giai đoạn render.
- **Monitors**: FPS, bộ nhớ, số object, draw call, physics, navigation, audio.
- **Video RAM**: dung lượng texture/mesh trên GPU.
- **Remote scene tree**: menu *Debug → Remote* trong editor xem cây node của game đang chạy và sửa property trực tiếp.

### 7.2 Debug đồ họa

| Công cụ | Nền tảng | Cách dùng |
| :--- | :--- | :--- |
| `--gpu-validation` + `--gpu-abort` | Vulkan / D3D12 / Metal | Bật validation layer, dừng ngay tại lệnh lỗi |
| **RenderDoc** | Windows, Linux (Vulkan/D3D12/GL) | Launch qua RenderDoc với args `--path <project> --rendering-driver vulkan`, chụp frame bằng F12 |
| **Xcode Metal Frame Capture** | macOS / iOS | Chạy dưới Xcode, *Debug → Capture GPU Workload* |
| **PIX** | Windows (D3D12) | Cài qua `install_d3d12_sdk_windows.py`, build `d3d12=yes` |
| Editor *Debug Draw* | Tất cả | Viewport 3D → Display Overdraw / Unshaded / Wireframe / các buffer GI, SSAO… |

Đổi renderer để khoanh vùng lỗi: chạy lần lượt `--rendering-method forward_plus`, `mobile`, `gl_compatibility`.

### 7.3 Profiler CPU (C++)

Build kèm profiler:

```bash
scons target=editor dev_build=yes debug_symbols=yes profiler=tracy profiler_path=/path/to/tracy
```

Các vùng đo trong engine dùng macro `GodotProfileZone(...)` (ví dụ trong `Main::iteration`). Trên macOS có thể dùng `profiler=instruments` để xem trong Instruments.

### 7.4 Sanitizer

```bash
scons target=editor dev_build=yes debug_symbols=yes use_asan=yes use_ubsan=yes
```

Chạy binary như bình thường; khi có lỗi bộ nhớ, ASAN in stack trace chi tiết và dừng chương trình.

---

## 8. Unit test

Engine dùng **doctest** (`thirdparty/doctest`), test nằm trong `tests/` và `modules/*/tests/`.

Build kèm test:

```bash
scons target=editor dev_build=yes tests=yes
```

Chạy toàn bộ test:

```bash
bin/bamboo.macos.editor.dev.arm64 --test
```

Chạy theo bộ lọc (cú pháp doctest):

```bash
bin/bamboo.macos.editor.dev.arm64 --test --test-case="*String*"
```

```bash
bin/bamboo.macos.editor.dev.arm64 --test --test-suite="[Navigation]*"
```

Thêm test mới: tạo file `tests/<khu-vực>/test_<tên>.h` theo mẫu các file hiện có (`TEST_CASE("[Tag] Mô tả") { CHECK(...); }`) và include vào `tests/test_main.cpp` nếu thư mục đó chưa được tự động gom.

---

## 9. Build export template (bản chạy game)

Export template là binary không có editor, dùng khi xuất game.

Bản debug (có debugger, log):

```bash
scons platform=macos arch=arm64 target=template_debug
```

Bản release:

```bash
scons platform=macos arch=arm64 target=template_release production=yes
```

Bản release tối ưu dung lượng — xem các cờ cắt giảm trong [ENGINE_ANALYSIS.md §4.1](ENGINE_ANALYSIS.md):

```bash
scons platform=windows target=template_release production=yes optimize=size_extra lto=full deprecated=no
```

Trong editor: *Project → Export → (preset) → Custom Template* trỏ tới file trong `bin/`.

Kiểm tra cấu hình ClassDB bị tắt khi dùng build profile: `scons ... build_profile=<file>.gdbuild` (tạo bằng *Project → Tools → Engine Compilation Configuration Editor*).

---

## 10. Code style & trước khi commit

- **C++**: `clang-format` theo `.clang-format`; kiểm tra tĩnh theo `.clang-tidy`.
- **Python** (SCons, script): `ruff` theo `pyproject.toml`.
- Dùng **pre-commit** (cấu hình trong `.pre-commit-config.yaml`):

```bash
python3 -m pip install pre-commit
```

```bash
pre-commit install
```

Chạy thủ công trên toàn bộ file đã đổi:

```bash
pre-commit run --all-files
```

Checklist trước khi tạo PR:

1. Build sạch với `dev_build=yes` không có warning mới (CI dùng `dev_mode=yes` → `werror=yes`).
2. Chạy `--test` liên quan đến khu vực đã sửa.
3. Chạy thử ít nhất một project mẫu trên renderer bị ảnh hưởng.
4. `pre-commit run` không báo lỗi.
5. Nếu sửa API công khai (`ClassDB`), cập nhật tài liệu XML trong `doc/classes/` (hoặc `modules/<name>/doc_classes/`) bằng `--doctool`.

---

## 11. Xử lý sự cố thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
| :--- | :--- | :--- |
| `scons: command not found` | Chưa cài SCons hoặc chưa có trong PATH | `python3 -m pip install scons`, kiểm tra PATH của pip |
| `MoltenVK SDK installation directory not found` (macOS) | Bật Vulkan nhưng chưa có Vulkan SDK | Cài bằng `install_vulkan_sdk_macos.sh`, chỉ định `vulkan_sdk_path=…`, hoặc build `vulkan=no` (dùng Metal) |
| Cảnh báo AccessKit / ANGLE không tìm thấy | Chưa chạy script cài dependency | Chạy `install_accesskit.py` / `install_angle.py`, hoặc bỏ qua (tính năng tự tắt), hoặc `accesskit=no angle=no` |
| Build hết RAM, bị kill | Quá nhiều job song song / `scu_build` | Giảm luồng: `scons -j4`, hoặc `scu_limit=…` |
| Linker rất chậm (Linux) | Dùng linker mặc định | `linker=mold` hoặc `linker=lld` |
| Breakpoint không dừng khi bấm Run trong editor | Game chạy trong process con | Debug bằng cấu hình chạy thẳng project hoặc attach vào process con (§6.1) |
| Không thấy log trên Windows | Bản GUI không có console | Dùng file `.console.exe` |
| Lỗi đồ họa chỉ xảy ra trên một máy | Driver GPU / API | Chạy với `--gpu-validation --verbose`, thử `--rendering-driver` khác |
| clangd báo lỗi include sai | Thiếu / cũ `compile_commands.json` | Build lại với `compiledb=yes` (hoặc `compiledb_gen_only=yes` để chỉ sinh file) |
| Build sau khi đổi nhánh lỗi lạ | Object file cũ | `scons --clean` cho cấu hình đó, hoặc xóa `bin/obj/` |

---

## 12. Quy ước riêng của Bamboo

- **Code mới của Bamboo** ưu tiên đặt trong custom module ngoài lõi:

```bash
scons target=editor dev_build=yes custom_modules=../bamboo_modules
```

- Mọi chỉnh sửa trực tiếp vào code Godot gốc (`core/`, `servers/`, `scene/`, `drivers/`, `platform/`) đánh dấu bằng comment `// BAMBOO:` và gom vào commit riêng theo tính năng, để dễ rebase khi cập nhật Godot upstream.
- Class mới đăng ký vào `ClassDB` dùng prefix `Bm` (ví dụ `BmVirtualCamera3D`), không đổi tên class có sẵn của Godot.
- Cấu hình build dùng chung cho team đặt trong `profiles/*.py` (cần tạo); cấu hình cá nhân để ở `custom.py` (đã có trong `.gitignore`, không commit).
