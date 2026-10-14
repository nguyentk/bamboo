# Bamboo Engine 0.1.0-beta.1 "Sprout" — Ghi chú phát hành (bản Beta nội bộ)

> Build ngày 14/10/2026 tại máy dev (macOS, Apple M4). **Chưa gắn tag git, chưa có nhánh `release/0.1`.**
> Dựa trên Godot Engine 4.8-dev (`c24bf5d933`). Bamboo Engine is based on Godot Engine.

## Gói cài đặt (`bin/release/`, kiểm tra bằng `SHA256SUMS.txt`)

| File | Nền tảng | Ghi chú |
| :--- | :--- | :--- |
| `Bamboo_v0.1.0-beta.1_macOS.dmg` | macOS universal (Apple Silicon + Intel) | Ký ad-hoc, **chưa notarize**. |
| `Bamboo_v0.1.0-beta.1_win64_setup.exe` | Windows 10/11 x86_64 | Bộ cài NSIS (không cần admin, EN/VI). **Chưa ký Authenticode.** |
| `Bamboo_v0.1.0-beta.1_win64.zip` | Windows 10/11 x86_64 | Bản portable. |
| `Bamboo_v0.1.0-beta.1_export_templates.tpz` | — | Templates macOS (universal) + Windows x86_64. |

## Thay đổi so với 0.1.0-alpha.3

- Phiên bản `0.1.0-beta.1`.
- **Bug bash tự động** (`misc/scripts/run_bug_bash.py`, `tests/bug_bash/`): editor, export, 15 tổ hợp scene × renderer,
  stress vật lý Jolt 1 000 vật thể, soak test 15 phút cho game dogfood. Kết quả: **0 P0, 0 P1, 0 P2, 4 P3** (đều nghi do upstream),
  2 hạng mục bị chặn (Linux/Android). Xem `docs/reports/bug_bash_0.1.0-beta.1.md`.
- Game dogfood: `tests/soak_test.gd` (autopilot, sinh lại coin, theo dõi FPS/bộ nhớ).
- Báo cáo parity có số liệu phía Bamboo (chưa có đối chứng Unity).

## Kiểm chứng

| Hạng mục | Kết quả |
| :--- | :--- |
| C++ doctest | 1436/1436 pass |
| Python tooling | 216 pass, 3 skip |
| Smoke test editor (arm64 + x86_64) + 4 templates macOS | PASS |
| Dogfood: gameplay 11/11, crash reporter 8/8 (`bamboo_version = 0.1.0-beta.1`) | PASS |
| Dogfood PC: 60 FPS (VSync), soak 15 phút: bộ nhớ +0,051 MiB/phút | PASS |
| Golden image (11), benchmark so với baseline | PASS / không hồi quy |
| Audit `BAMBOO:` | 94/94 |

## Hạn chế đã biết

- macOS: renderer Compatibility không giữ VSync (~120 FPS trên màn 60 Hz); Forward+ bỏ qua `--disable-vsync` (BB-1, BB-2).
- Lần chạy đầu sau khi cài bản mới có thể khựng ~1,3 s ở frame đầu (biên dịch shader Metal, BB-3).
- Windows: tắt D3D12, AccessKit, ANGLE; chưa chạy thử trên máy Windows thật.
- Chưa có bản Android/Linux/Web; game dogfood là dự án mẫu, chưa phải game Unity được port.
