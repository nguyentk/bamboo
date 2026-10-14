# Bamboo Engine 0.1.0-alpha.2 "Sprout" — Ghi chú phát hành (bản thử nghiệm nội bộ)

> Build ngày 13/10/2026 tại máy dev (macOS, Apple M4). **Chưa gắn tag git, chưa phát hành công khai.**
> Dựa trên Godot Engine 4.8-dev (`c24bf5d933`). Bamboo Engine is based on Godot Engine.

## Gói cài đặt (`bin/release/`, kiểm tra bằng `SHA256SUMS.txt`)

| File | Nền tảng | Ghi chú |
| :--- | :--- | :--- |
| `Bamboo_v0.1.0-alpha.2_macOS.dmg` | macOS 64-bit universal (Apple Silicon + Intel) | Kéo `Bamboo.app` vào Applications. Ký ad-hoc, **chưa notarize**: lần đầu mở bằng chuột phải → Open. |
| `Bamboo_v0.1.0-alpha.2_win64_setup.exe` | Windows 10/11 x86_64 | Bộ cài NSIS, cài cho người dùng hiện tại (không cần admin), tiếng Anh + tiếng Việt, có gỡ cài đặt. **Chưa ký Authenticode**: SmartScreen sẽ cảnh báo. |
| `Bamboo_v0.1.0-alpha.2_win64.zip` | Windows 10/11 x86_64 | Bản portable (editor + console wrapper). |
| `Bamboo_v0.1.0-alpha.2_export_templates.tpz` | — | Export templates macOS (universal) + Windows x86_64 (debug/release + console wrapper). Editor → Manage Export Templates → Install From File. |

Không có trong bản này: Linux, Android, iOS, Web (build qua CI).

## Thay đổi so với 0.1.0-alpha.1

- Phiên bản `0.1.0-alpha.2` (Godot base giữ `4.8`, tương thích GDExtension).
- Export templates **Windows** có trong `.tpz` (kèm `*_console.exe` cho tùy chọn *Export Console Wrapper*).
- macOS: bundle editor tên `Bamboo.app` (trước đây file chạy tên `Godot`), editor và templates universal.
- Windows: bộ cài NSIS (`misc/dist/windows/bamboo_installer.nsi`, `misc/scripts/package_windows.sh`).
- CI: workflow nightly `bamboo_nightly.yml` chạy benchmark + golden image trên Linux (llvmpipe/lavapipe) và macOS (Metal), baseline riêng từng runner.
- Benchmark baseline mới cho `0.1.0-alpha.2` (`benchmarks/baseline.json`).

## Kiểm chứng

| Hạng mục | Kết quả |
| :--- | :--- |
| C++ doctest (bản `tests=yes`) | 1436/1436 pass |
| Python tooling | 205 test pass, 3 skip (PyYAML, GUI, GitHub) |
| Smoke test editor (arm64 + x86_64 qua Rosetta), 4 templates macOS | PASS |
| Golden image Metal (11 ảnh) | 0.000% khác biệt |
| Benchmark so với baseline alpha.1 | Không hồi quy |
| Export game dogfood bằng templates mới | macOS (universal, chạy được) và Windows (`.exe` PE x86-64) |

## Hạn chế đã biết

- Bản Windows tắt D3D12 (thiếu Agility SDK), AccessKit (trình đọc màn hình) và ANGLE; editor dùng Vulkan / OpenGL.
- **Bộ cài và game xuất ra cho Windows chưa được chạy trên máy Windows thật** (build chéo từ macOS).
- Icon vẫn là logo Godot (chưa có bộ nhận diện Bamboo).
- Build tắt LTO (`lto=none`).
