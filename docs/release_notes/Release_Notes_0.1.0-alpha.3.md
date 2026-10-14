# Bamboo Engine 0.1.0-alpha.3 "Sprout" — Ghi chú phát hành (bản thử nghiệm nội bộ)

> Build ngày 14/10/2026 tại máy dev (macOS, Apple M4). **Chưa gắn tag git, chưa phát hành công khai.**
> Dựa trên Godot Engine 4.8-dev (`c24bf5d933`). Bamboo Engine is based on Godot Engine.

## Gói cài đặt (`bin/release/`, kiểm tra bằng `SHA256SUMS.txt`)

| File | Nền tảng | Ghi chú |
| :--- | :--- | :--- |
| `Bamboo_v0.1.0-alpha.3_macOS.dmg` | macOS universal (Apple Silicon + Intel) | Ký ad-hoc, **chưa notarize** (lần đầu: chuột phải → Open). |
| `Bamboo_v0.1.0-alpha.3_win64_setup.exe` | Windows 10/11 x86_64 | Bộ cài NSIS, không cần admin, EN/VI. **Chưa ký Authenticode.** |
| `Bamboo_v0.1.0-alpha.3_win64.zip` | Windows 10/11 x86_64 | Bản portable. |
| `Bamboo_v0.1.0-alpha.3_export_templates.tpz` | — | Templates macOS (universal) + Windows x86_64 (debug/release + console wrapper). |

## Thay đổi so với 0.1.0-alpha.2

- **Profile build 2D** (`profiles/bamboo_2d.py`) dùng `optimize=size`: template release macOS arm64 **41.3 MB, −30%** so với bản
  đầy đủ (trước: −17%), vẫn giữ shaping chữ phức tạp và API deprecated. Xem `docs/reports/binary_size_benchmark.md`.
- Diễn tập rebase lần 2 lên upstream mới nhất (743 commit): 5 khối xung đột, bản rebase build được và pass 1445/1445 test C++.
  Xem `docs/rebase_reports/rebase_rehearsal_20261014.md`.

## Kiểm chứng

| Hạng mục | Kết quả |
| :--- | :--- |
| C++ doctest | 1436/1436 pass (`[BambooVersion]`, `[JoltPhysics]`, `[Regression]` 9/9) |
| Python tooling | 205 pass, 3 skip |
| Smoke test: editor (arm64 + x86_64), 4 templates macOS, template 2D | PASS |
| Game dogfood: gameplay 11/11, crash reporter 8/8; export macOS (chạy được) + Windows | PASS |
| Golden image Metal (11 ảnh) | PASS |
| Benchmark so với baseline alpha.2 | Không hồi quy |
| Audit `BAMBOO:` | 93/93 |

## Hạn chế đã biết

- Bản Windows tắt D3D12, AccessKit, ANGLE; **chưa chạy thử trên máy Windows thật** (build chéo từ macOS).
- Profile Mobile mới giảm 18.9% (mục tiêu sprint 20%).
- Game dogfood là dự án mẫu, chưa phải game Unity nội bộ được port.
- Icon vẫn là logo Godot; build tắt LTO.
