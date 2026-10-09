# 🎋 Bamboo Engine — Multi-Agent Prompt System (Claude Code & Antigravity)

> Hệ thống phân công nhiệm vụ và điều phối Multi-Agent cho dự án **Bamboo Game Engine** (dựa trên Godot 4.8.dev), phục vụ thực thi roadmap Q4/2026 hướng tới bản phát hành chính thức **Bamboo 0.1.0 "Sprout"**.

---

## 1. Cơ chế Điều phối Multi-Agent (Claude Code & Antigravity)

Hệ thống được thiết kế theo mô hình **Role-Based Multi-Agent Collaboration**:

| Ký hiệu | Vai trò Agent | Trách nhiệm chính |
| :---: | :--- | :--- |
| **TL** | **Tech Lead / Orchestrator** | Quản lý branching, review PR, triage lỗi P0-P3, điều phối release, diễn tập upstream rebase. |
| **BQ** | **Build & CI / QA** | Cấu hình GitHub Actions, SCons caching, đóng gói export templates (`.tpz`), ký số, packaging (.dmg/.zip). |
| **RND** | **Rendering Engine** | Golden-image regression tests (3 renderers), shader warming, benchmark draw-calls. |
| **RT** | **Runtime & Physics** | Tích hợp Jolt Physics mặc định, GDScript/AOT profiling, micro-benchmarks, math & core doctests. |
| **PLT** | **Platform & Mobile** | Hỗ trợ Android (APK/AAB), iOS, Web (Wasm), thiết lập toolchain mobile, build profiles. |
| **TLS** | **Tools & Editor** | UI editor branding, versioning button, project manager, exporter, localization (.pot). |
| **GAME** | **Dogfooding & Unity Porting** | Khảo sát, thiết kế pipeline và port trực tiếp ≥ 1 game nội bộ từ Unity3D sang Bamboo Engine. |

---

## 2. Cấu trúc Thư mục Prompts Theo Chu kỳ 2 Tuần / Bản Build

Mỗi thư mục đại diện cho **1 Sprint (2 tuần)** tương ứng với 1 mốc phát hành trên roadmap:

```
.prompts/
├── README.md                              # Tài liệu điều phối tổng quan (file này)
│
├── 0.1.0-alpha.1/                         # SPRINT 1 (W1 – W2 · 12/10 – 23/10) — Khởi động, CI Desktop, Unity Survey
│   ├── AGENT_COORDINATION.md              # Phân công & luồng phối hợp giữa các Agent trong Sprint 1
│   ├── PROMPT_TL_SETUP_AND_BRANCHING.md   # TL: Branching, chuẩn hóa môi trường, triage board
│   ├── PROMPT_BQ_DESKTOP_CI_AND_TEMPLATES.md # BQ: CI Desktop (Win/Mac/Linux), tắt update Godot, gói .tpz
│   ├── PROMPT_TLS_VERSIONING_AND_TESTS.md # TLS: C++ Versioning tests (doctest), editor version string
│   └── PROMPT_GAME_UNITY_SURVEY_PIPELINE.md # GAME/PLT: Khảo sát game Unity nội bộ, schema mapping
│
├── 0.1.0-alpha.2/                         # SPRINT 2 (W3 – W4 · 26/10 – 06/11) — CI Mobile/Web, Benchmarks, Asset Converter
│   ├── AGENT_COORDINATION.md              # Phân công & luồng phối hợp Sprint 2
│   ├── PROMPT_PLT_MOBILE_WEB_CI.md        # PLT/BQ: CI Android APK/AAB, iOS, Web & Code signing
│   ├── PROMPT_RT_RND_BENCHMARK_SUITE.md   # RT/RND: Benchmark headless project, JSON output & tests
│   ├── PROMPT_RND_GOLDEN_IMAGE_TESTS.md   # RND: Golden image rendering test 3 renderer & doctests
│   └── PROMPT_GAME_UNITY_ASSET_CONVERTER.md # GAME/TLS: Pipeline convert asset Unity (models/textures/prefabs)
│
├── 0.1.0-alpha.3/                         # SPRINT 3 (W5 – W6 · 09/11 – 20/11) — Upstream Rebase, Jolt Default, Profiles
│   ├── AGENT_COORDINATION.md              # Phân công & luồng phối hợp Sprint 3
│   ├── PROMPT_TL_UPSTREAM_REBASE_REHEARSAL.md # TL: Diễn tập rebase Godot master, kiểm kê // BAMBOO:
│   ├── PROMPT_RT_JOLT_DEFAULT_AND_TESTS.md    # RT: Jolt 3D Physics làm mặc định & C++ doctests
│   ├── PROMPT_BQ_BUILD_PROFILES.md            # BQ/PLT: 3 Build profiles (2D, Mobile, PC) & test kiểm chứng
│   └── PROMPT_GAME_UNITY_LOGIC_AND_SCENE.md   # GAME/RT: Ánh xạ MonoBehaviour -> Bamboo Script/Signal & Scene
│
├── 0.1.0-beta.1/                          # SPRINT 4 (W7 – W8 · 23/11 – 04/12) — Hoàn tất Port Game, Bug Bash, Freeze
│   ├── AGENT_COORDINATION.md              # Phân công & luồng phối hợp Sprint 4
│   ├── PROMPT_GAME_RUN_AND_VALIDATE.md        # GAME: Game chạy thực tế PC+Android, telemetry & crash log
│   ├── PROMPT_ALL_BUG_BASH_AND_TRIAGE.md      # ALL: Bug bash toàn diện 2 ngày, triage & cherry-pick
│   ├── PROMPT_RT_UNITY_PARITY_BENCHMARK.md    # RT/GAME: Báo cáo baseline hiệu năng & so sánh Unity
│   └── PROMPT_TL_FEATURE_FREEZE.md            # TL: Tách nhánh release/0.1, đóng băng tính năng
│
└── 0.1.0/                                 # SPRINT 5 (W9 – W10 · 07/12 – 18/12) — Ổn định, Packaging, GA Release "Sprout"
    ├── AGENT_COORDINATION.md              # Phân công & luồng phối hợp Sprint 5
    ├── PROMPT_ALL_P0_BUG_FIXES.md             # ALL: Triệt tiêu 100% bug P0/P1 trên release branch
    ├── PROMPT_BQ_PACKAGING_NOTARIZATION.md    # BQ: Đóng gói .dmg notarized, .zip, .tpz templates
    ├── PROMPT_TLS_LOCALIZATION_AND_DOCS.md    # TLS: String freeze, cập nhật .pot, tài liệu Migration Unity
    └── PROMPT_TL_GO_NOGO_AND_RELEASE.md       # TL: Go/No-go meeting, tag bamboo-v0.1.0, release notes GA
```

---

## 3. Quy tắc Kỹ thuật Bắt buộc Cho Mọi Prompts

### 3.1 Tech Stack & Build Toolchain
* **Ngôn ngữ lõi**: C++17 (SCons build system trên Python 3.9+).
* **Môi trường biên dịch**:
  * macOS: `clang` / `AppleClang` (`scons platform=macos target=editor arch=arm64`).
  * Linux: `gcc` / `clang` (`scons platform=linuxbsd target=editor`).
  * Windows: `MSVC 2022` hoặc `x86_64-w64-mingw32-gcc`.
* **Testing Framework**: **doctest** tích hợp sẵn trong Godot/Bamboo tại `tests/test_macros.h`.
  * Chạy test: `scons platform=<os> tests=yes` -> `bin/bamboo.<os>.editor.<arch> --test`.

### 3.2 Quy chuẩn Mã nguồn & Bản quyền
1. **Bảo toàn Bản quyền MIT**: Tuyệt đối không xóa hoặc chỉnh sửa header bản quyền gốc (`// Copyright (c) 2014-present Godot Engine contributors...`).
2. **Không sửa thư mục `thirdparty/`**: Giữ nguyên vẹn toàn bộ submodule và mã nguồn bên thứ 3.
3. **Quy ước Patch `// BAMBOO:`**: Mọi sửa đổi trực tiếp vào core/servers/scene/editor **bắt buộc** phải được bao bọc hoặc đánh dấu bằng comment `// BAMBOO: ...`.
4. **Bảo toàn GDExtension ABI**: Giữ nguyên `major=4`, `minor=8`, `patch=0` trong `version.py`; mọi định danh Bamboo dùng `bamboo_*`.

---

## 4. Hướng dẫn Chạy Prompt với Claude Code & Antigravity

### Với Claude Code (CLI):
```bash
# Thực thi prompt cụ thể cho một Agent trong Sprint
claude --prompt "$(cat .prompts/0.1.0-alpha.1/PROMPT_TLS_VERSIONING_AND_TESTS.md)"
```

### Với Antigravity:
Mở Antigravity IDE, chọn file prompt mong muốn trong `.prompts/<milestone>/` và giao task cho agent phụ trách.
Mỗi task phải tuân thủ chu trình: **Phân tích codebase → Hiện thực code → Viết Unit Test → Biên dịch & Chạy Test → Đánh giá Exit Criteria**.
