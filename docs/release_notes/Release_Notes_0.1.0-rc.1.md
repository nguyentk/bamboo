# Bamboo Engine 0.1.0-rc.1 "Sprout" — Ghi chú phát hành (bản ứng viên nội bộ)

> Build ngày 15/10/2026 tại máy dev (macOS, Apple M4) từ nhánh `release/0.1`. Họp Go/No-go: **NO-GO** cho bản chính thức
> ([biên bản](../reports/go_nogo/go_nogo_0.1.0.md)); rc.1 dùng nội bộ để kiểm thử.
> Dựa trên Godot Engine 4.8-dev (`c24bf5d933`). Bamboo Engine is based on Godot Engine.

## Gói cài đặt (`bin/release/`, kiểm tra bằng `SHA256SUMS.txt`)

| File | Nền tảng | Ghi chú |
| :--- | :--- | :--- |
| `Bamboo_v0.1.0-rc.1_macOS.dmg` | macOS universal (Apple Silicon + Intel) | Ký ad-hoc, **chưa notarize** (lần đầu: chuột phải → Open). |
| `Bamboo_v0.1.0-rc.1_win64_setup.exe` | Windows 10/11 x86_64 | Bộ cài NSIS (không cần admin, EN/VI). **Chưa ký Authenticode.** |
| `Bamboo_v0.1.0-rc.1_win64.zip` | Windows 10/11 x86_64 | Bản portable. |
| `Bamboo_v0.1.0-rc.1_export_templates.tpz` | — | Templates macOS (universal) + Windows x86_64. |

## Thay đổi so với 0.1.0-beta.1

- Phiên bản `0.1.0-rc.1`.
- Sửa lỗi CI: Gradle đọc `version.py` (Android), thư mục test regression trong build SCU, kiểm tra style (BAMBOO-REG-3/4).
- `check_open_issues.py`: báo lỗi khi GitHub Issues bị tắt thay vì "0 P0"; tự dùng `curl` khi Python thiếu chứng chỉ CA (BAMBOO-101).
- Hướng dẫn Unity → Bamboo: cập nhật số liệu profile 2D (41,3 MB, −30%).

## Kiểm chứng

C++ 1436/1436 · smoke test editor + 4 templates macOS · dogfood gameplay 11/11, crash reporter 8/8 · golden image 11/11 ·
benchmark: RAM không đổi, FPS trong biên độ nhiễu · CI 23/23 trên `release/0.1` (trước khi nâng rc.1).

## Hạn chế đã biết

Như beta.1 (VSync macOS, khựng shader lần đầu, Windows chưa chạy trên máy thật, chưa có Android/Linux/Web, chưa ký số),
cộng BB-5 (lỗi `singleton is null` ngẫu nhiên khi export headless, không ảnh hưởng kết quả).
