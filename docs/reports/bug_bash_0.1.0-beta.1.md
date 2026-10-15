# Bug bash tự động — Bamboo 0.1.0-beta.1

> Sinh bởi `misc/scripts/run_bug_bash.py` · binary `bin/bamboo.macos.editor.arm64` · darwin, arm64.
> Mức độ gán tự động theo quy tắc trong script; TL rà lại trước khi tạo issue.

## Tổng hợp

| P0 | P1 | P2 | P3 | Blocked | Pass |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 5 | 2 | 27 |

## Phát hiện (không tính pass)

| Mức | Khu vực | Kiểm tra | Mô tả |
| :--- | :--- | :--- | :--- |
| P3 | rendering | `test_pbr_materials.tscn:gl_compatibility` | VSync on but 108.4 FPS on a 60 Hz display |
| P3 | rendering | `test_shadow_mapping.tscn:gl_compatibility` | VSync on but 117.8 FPS on a 60 Hz display |
| P3 | rendering | `test_alpha_blending.tscn:gl_compatibility` | VSync on but 116.2 FPS on a 60 Hz display |
| P3 | rendering | `test_canvas_item_2d.tscn:gl_compatibility` | VSync on but 118.2 FPS on a 60 Hz display |
| P3 | rendering | `main_level.tscn:gl_compatibility` | VSync on but 117.0 FPS on a 60 Hz display |
| blocked | export | `export:Linux` | templates not installed: linux_release.x86_64 |
| blocked | export | `export:Android` | templates not installed: android_release.apk, android_source.zip |

## Tất cả kiểm tra

| Khu vực | Kiểm tra | Kết quả | Mô tả |
| :--- | :--- | :--- | :--- |
| editor | `version_header` | pass | Bamboo Engine v0.1.0-beta.1 (Godot 4.8.dev.bamboo.1d681cd05) (2026-10-09 09:13:23 UTC) - https://godotengine.org |
| editor | `open_project:game_dogfood` | pass | opens without errors |
| editor | `open_project:benchmarks` | pass | opens without errors |
| editor | `open_project:tests/visual` | pass | opens without errors |
| editor | `open_project:tests/bug_bash` | pass | opens without errors |
| editor | `open_new_empty_project` | pass | new project opens |
| export | `export:macOS` | pass | exported |
| export | `export:Windows Desktop` | pass | exported |
| export | `export:Linux` | blocked | templates not installed: linux_release.x86_64 |
| export | `export:Android` | blocked | templates not installed: android_release.apk, android_source.zip |
| rendering | `test_pbr_materials.tscn:forward_plus` | pass | 60.0 FPS, warm-up worst 21.27 ms |
| rendering | `test_pbr_materials.tscn:mobile` | pass | 60.0 FPS, warm-up worst 21.31 ms |
| rendering | `test_pbr_materials.tscn:gl_compatibility` | P3 | VSync on but 108.4 FPS on a 60 Hz display |
| rendering | `test_shadow_mapping.tscn:forward_plus` | pass | 60.0 FPS, warm-up worst 27.15 ms |
| rendering | `test_shadow_mapping.tscn:mobile` | pass | 60.0 FPS, warm-up worst 22.54 ms |
| rendering | `test_shadow_mapping.tscn:gl_compatibility` | P3 | VSync on but 117.8 FPS on a 60 Hz display |
| rendering | `test_alpha_blending.tscn:forward_plus` | pass | 60.0 FPS, warm-up worst 20.73 ms |
| rendering | `test_alpha_blending.tscn:mobile` | pass | 60.0 FPS, warm-up worst 21.53 ms |
| rendering | `test_alpha_blending.tscn:gl_compatibility` | P3 | VSync on but 116.2 FPS on a 60 Hz display |
| rendering | `test_canvas_item_2d.tscn:forward_plus` | pass | 60.0 FPS, warm-up worst 20.23 ms |
| rendering | `test_canvas_item_2d.tscn:mobile` | pass | 60.0 FPS, warm-up worst 20.57 ms |
| rendering | `test_canvas_item_2d.tscn:gl_compatibility` | P3 | VSync on but 118.2 FPS on a 60 Hz display |
| rendering | `main_level.tscn:forward_plus` | pass | 60.0 FPS, warm-up worst 21.28 ms |
| rendering | `main_level.tscn:mobile` | pass | 60.0 FPS, warm-up worst 23.47 ms |
| rendering | `main_level.tscn:gl_compatibility` | P3 | VSync on but 117.0 FPS on a 60 Hz display |
| physics | `physics_engine_is_jolt` | pass | ok |
| physics | `stack_no_tunneling_or_nan` | pass | ok |
| physics | `stack_physics_time` | pass | ok |
| physics | `raycast_hits_thin_wall_both_sides` | pass | ok |
| physics | `ccd_prevents_tunneling` | pass | ok |
| physics | `area_body_entered_signal` | pass | ok |
| physics | `rigid_body_entered_signal` | pass | ok |
| game | `dogfood_fps_windowed` | pass | median 60 FPS, min 60.0 FPS |
| game | `dogfood_soak_headless` | pass | 900.0 s, memory 0.051 MiB/min, 538 coins |

## Điều tra thủ công & triage (TL, 14/10/2026)

Môi trường: MacBook Air Apple M4, màn hình tích hợp + Dell P2217H, **cả hai 60 Hz**. Bản build `0.1.0-beta.1` production.

| ID | Mức | Vấn đề | Bằng chứng | Nguồn gốc (dự đoán) | Kế hoạch |
| :--- | :--- | :--- | :--- | :--- | :--- |
| BB-1 | P3 | Renderer Compatibility (OpenGL) trên macOS không giữ VSync: ~120 FPS trên màn 60 Hz | 5/5 scene ở trên; `--print-fps`: VSync bật 120 FPS, `--disable-vsync` 449 FPS | Upstream (Bamboo không sửa phần render) | Sprint 5: đối chiếu với Godot upstream cùng commit; nếu tái hiện, báo upstream; ghi vào "Hạn chế đã biết" |
| BB-2 | P3 | Forward+ (Metal) bỏ qua `--disable-vsync`: vẫn 60 FPS | `--print-fps`: 60 FPS cả khi tắt VSync | Upstream | Như BB-1 (ảnh hưởng benchmark GPU uncapped, không ảnh hưởng người chơi) |
| BB-3 | P3 | Lần chạy đầu sau khi cài binary mới: frame đầu tiên 1,3 s (Forward+) | 1 287 ms khi chạy alpha.3 lần đầu; xóa cache shader của game chỉ còn 43 ms → do cache Metal của hệ điều hành | Upstream / hệ điều hành | Q1/2027: shader pre-warming khi khởi động (đúng hạng mục trong báo cáo parity) |
| BB-4 | P3 | Compatibility mất ~200 ms biên dịch shader mỗi lần chạy (không có cache) | warm-up 200 ms cả khi cache "ấm" | Upstream | Theo dõi; ưu tiên Forward+/Mobile cho PC/Android |
| BB-5 | P3 | `ERROR: Parameter "singleton" is null.` trong 1/31 lần export headless (rc.1, 15/10) | Export vẫn thành công, game chạy được; 30 lần chạy lại không tái hiện, không lấy được vị trí | Chưa rõ (vị trí khả dĩ: các `finalize_*` khi tắt engine) | Theo dõi trong CI/bug bash tiếp theo; lưu toàn bộ log khi xuất hiện |
| B-1 | blocked | Export Linux chưa kiểm tra | Thiếu template Linux (cần CI) | — | Chạy lại sau khi CI sinh template Linux |
| B-2 | blocked | Export / chạy Android chưa kiểm tra | Thiếu NDK 29 + template Android + thiết bị | — | Cần cài NDK và thiết bị Android tầm trung |

**Không có lỗi P0/P1** trong các khu vực chạy tự động được → không cần bản sửa / regression test mới trong đợt này.
Các lỗi thật tìm được trước đó đã có regression test: `BAMBOO-REG-1` (header phiên bản sinh ra), `BAMBOO-REG-2` (xem `tests/regression/README.md`).

### Chưa bao phủ (cần người kiểm thử)

- Editor GUI: tạo project từ Project Manager, đổi tên file, kéo-thả node, import tài nguyên lớn, hộp thoại About.
- Chơi tay toàn bộ màn trên PC và Android; export iOS / Web (chưa có preset và template).
- Windows: bộ cài và game xuất ra mới chỉ build chéo, chưa chạy trên máy Windows.
