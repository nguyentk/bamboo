# Bamboo — Đo kích thước binary theo build profile (cập nhật 14/10/2026, `0.1.0-alpha.3`)

> Sprint `0.1.0-alpha.3` · BQ. Template release macOS arm64, Apple Clang 21. Sinh bảng bằng
> `python3 misc/scripts/measure_binary_sizes.py --bin-dir bin --output <file>` (bảng dưới chỉ giữ các template release; MB = MiB).
> Mục tiêu: profile 2D nhỏ hơn bản đầy đủ **≥ 25%** (Sprint DoD: 20–35% cho 2D/Mobile).

## Kết quả

| Binary | Profile | Size (MB) | Zip (MB) | vs. bản đầy đủ | Đạt mục tiêu? |
| :--- | :--- | ---: | ---: | ---: | :---: |
| `bamboo.macos.template_release.arm64` | đầy đủ (tham chiếu) | 58.9 | 20.7 | — | |
| `bamboo.macos.template_release.arm64.pc` | `pc` | 58.9 | 20.7 | 0% | (không có mục tiêu) |
| `bamboo.macos.template_release.arm64.2d` | `2d` | **41.3** | 14.1 | **−30.0%** | ✅ |
| `bamboo.macos.template_release.arm64.mobile` | `mobile` | 47.8 | 16.4 | −18.9% | ❌ (dưới 20%) |
| `bamboo.macos.template_release.arm64.2d_min` | thử nghiệm (không phải profile) | 39.1 | 13.3 | −33.6% | — |

Smoke test template `2d` (nạp PCK, khởi động headless): **PASS**.

## Thay đổi so với lần đo 12/10

- `profiles/bamboo_2d.py` thêm `optimize = "size"` (-Os). Chỉ riêng việc tắt 3D cho −17%; thêm -Os đưa lên **−30%**.
- Không cần các đánh đổi của biến thể `2d_min`: profile 2D vẫn giữ text server nâng cao (shaping chữ Ả Rập, Thái…,
  BiDi) và các API deprecated, nên project/addon Godot 4.x hiện có vẫn chạy.
- Đánh đổi còn lại: -Os có thể chậm hơn chút ở phần CPU (script, physics 2D). Cần đo bằng `benchmarks/` trên bản
  template 2D khi có kịch bản benchmark dành cho template.

## Profile Mobile (−18.9%)

Mobile giữ cả 2D và 3D và đã dùng -Os, nên khó giảm thêm nếu không bỏ tính năng. Các hướng (cần GAME/PLT chọn theo game
thực tế): tắt module ít dùng trên mobile (`theora` video, `webxr`, `upnp`, `enet`…), hoặc `deprecated=no`, hoặc text server
fallback cho game chỉ dùng chữ Latin/tiếng Việt. Chưa áp dụng vì ảnh hưởng tới tính năng.
