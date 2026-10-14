# Unity vs Bamboo — Parity benchmark

> **Trạng thái: CHƯA CÓ SỐ LIỆU ĐỐI CHỨNG UNITY.** Chưa có game Unity nội bộ để port và đo, nên bảng dưới để trống.
> Không điền số ước lượng: báo cáo này chỉ được cập nhật từ dữ liệu đo bằng [`misc/scripts/compare_unity_bamboo_metrics.py`](../../misc/scripts/compare_unity_bamboo_metrics.py) (script từ chối ghi báo cáo từ dữ liệu `"sample": true`).

## 1. Quy trình đo

1. Chọn cùng một màn chơi, cùng số entity, cùng độ phân giải và chế độ VSync trên cả hai bản.
2. Thiết bị chuẩn: PC (Intel Core i7 / RTX 3060), Android (Snapdragon 778G). Sạc đầy, tắt ứng dụng nền, nhiệt độ máy ổn định.
3. Ghi 1.000 frame liên tục sau 10 giây warm-up:
   - Unity: Unity Profiler / `FrameTimingManager`, Memory Profiler, build Release (IL2CPP).
   - Bamboo: build `template_release`, `Performance` monitors (`TIME_PROCESS`, `RENDER_TOTAL_DRAW_CALLS_IN_FRAME`, `MEMORY_STATIC`), benchmark runner ([`benchmarks/`](../../benchmarks/)).
4. Cold startup: thời gian từ lúc chạm icon / chạy binary đến frame gameplay đầu tiên, trung vị 5 lần, sau khi khởi động lại máy.
5. Kích thước cài đặt: APK/AAB (Android) và thư mục cài đặt (PC), cùng cấu hình nén texture.
6. Ghi kết quả vào hai file JSON (`engine: "unity"` / `"bamboo"`, `"sample": false`), rồi:

```bash
python3 misc/scripts/compare_unity_bamboo_metrics.py --unity unity_pc.json --bamboo bamboo_pc.json --output docs/reports/unity_vs_bamboo_parity_report.md
```

## 2. Kết quả

| Metric | Unity | Bamboo | Bamboo vs Unity | Verdict |
| :--- | ---: | ---: | ---: | :--- |
| FPS average | — | — | — | — |
| FPS 1% low | — | — | — | — |
| Draw calls / frame | — | — | — | — |
| RAM usage | — | — | — | — |
| Install size | — | — | — | — |
| Cold startup | — | — | — | — |

## 3. Số liệu Bamboo đã đo được (không có đối chứng Unity)

Đo ngày 14/10/2026 trên game dogfood (dự án mẫu, **không phải game Unity được port**), bản `0.1.0-beta.1`,
MacBook Air Apple M4, màn hình 60 Hz. Chưa đo trên PC chuẩn (i7 / RTX 3060) và Android (Snapdragon 778G).

| Hạng mục | Giá trị | Cách đo |
| :--- | :--- | :--- |
| FPS (Forward+, VSync, 1280x720) | 60 trung vị, 60 thấp nhất (giới hạn bởi VSync) | `soak_test.gd` có cửa sổ, 60 s |
| Bộ nhớ tĩnh engine sau 15 phút chơi tự động | 89,7 MiB, tăng 0,051 MiB/phút (không rò rỉ) | `soak_test.gd` headless 900 s, 538 coin được sinh/nhặt |
| RAM tiến trình (max RSS), bản export release | 236 MiB | `/usr/bin/time -l`, 600 frame |
| Khởi động → frame thứ 2 → thoát, bản export release | 487–519 ms (trung vị 510 ms) | 5 lần; có 1 lần 10,8 s, nhiều khả năng do macOS quét app chưa ký lần đầu |
| Kích thước cài đặt macOS (universal arm64 + x86_64) | 123 MB `.app` (zip 44 MiB) | export template release |
| Kích thước cài đặt Windows x86_64 | 72 MiB (`.exe` + `.pck`) | export template release |
| Template release macOS arm64 (đầy đủ / 2D / Mobile) | 58,9 / 41,3 / 47,8 MiB | [binary_size_benchmark.md](binary_size_benchmark.md) |
| Vật lý Jolt: 1 000 RigidBody3D | physics p95 12 ms, không xuyên sàn | `tests/bug_bash/scripts/physics_stress.gd` |

## 4. Việc cần làm để hoàn thành

- [ ] Chọn game Unity nội bộ, chạy `tools/unity_importer/survey_unity_project.py`, chốt scope (GAME + TL).
- [ ] Port game, đo trên PC và Android theo mục 1.
- [ ] Sinh bảng mục 2 bằng script, bổ sung đánh giá vật lý (Jolt vs PhysX) và hạng mục cần tối ưu Q1/2027.
