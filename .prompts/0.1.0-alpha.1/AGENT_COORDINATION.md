# 🎋 Sprint Coordination: Bamboo 0.1.0-alpha.1 (W1 – W2)

> **Mục tiêu Sprint**: Thiết lập môi trường, CI Desktop (Win/macOS/Linux), chuẩn hóa Dual-Versioning (kèm Unit Tests), và khảo sát game Unity3D nội bộ.  
> **Thời gian**: 12/10/2026 – 23/10/2026  
> **Mốc phát hành**: **`Bamboo 0.1.0-alpha.1`** (Cuối W2 - 23/10/2026)

---

## 1. Phân công Vai trò & Nhiệm vụ

| Agent | File Prompt | Trách nhiệm chính |
| :---: | :--- | :--- |
| **TL** | `PROMPT_TL_SETUP_AND_BRANCHING.md` | Chiến lược branching (`bamboo/main`, `upstream/master`), checklist môi trường dev, triage board. |
| **BQ** | `PROMPT_BQ_DESKTOP_CI_AND_TEMPLATES.md` | CI Desktop matrix (Win/Mac/Linux), tắt update server Godot, đóng gói template offline `.tpz`. |
| **TLS** | `PROMPT_TLS_VERSIONING_AND_TESTS.md` | Cài đặt Dual-versioning (`version.py`, `core/version.h`), nút phiên bản Editor, **viết Unit Test doctest**. |
| **GAME** | `PROMPT_GAME_UNITY_SURVEY_PIPELINE.md` | Khảo sát game Unity nội bộ, lập tài liệu ánh xạ kiến trúc (Prefab -> PackedScene, Script -> Node/Signal). |

---

## 2. Luồng Phối hợp (Handoff Workflow)

```
[TL Agent: Setup & Branching]
       │
       ▼
 ┌─────┴────────────────────────────────┐
 │                                      │
 ▼                                      ▼
[TLS: Versioning & Unit Tests]     [GAME: Unity Project Survey]
 │                                      │
 └─────────────────┬────────────────────┘
                   │
                   ▼
         [BQ: Desktop CI & .tpz]
                   │
                   ▼
       [TAG: bamboo-v0.1.0-alpha.1]
```

1. **Bước 1 (TL)**: Khởi tạo nhánh `bamboo/main` sạch, hợp nhất code rebranding nền tảng, thiết lập nhãn issue P0–P3.
2. **Bước 2 (TLS & GAME chạy song song)**:
   - **TLS Agent**: Hoàn thiện các macro C++ versioning, expose ra `Engine.get_version_info()`, viết unit test doctest trong `tests/core/config/test_bamboo_version.cpp` và chạy passed 100%.
   - **GAME Agent**: Khảo sát mã nguồn game Unity3D nội bộ được chọn, lập danh mục asset, shader, C# scripts và sinh schema mapping `unity_to_bamboo_spec.json`.
3. **Bước 3 (BQ Agent)**: Dựng CI desktop trên `.github/workflows/`, tích hợp SCons caching, tắt `engine_update_check`, đóng gói `.tpz` templates offline.
4. **Bước 4 (TL & BQ Agent)**: Chạy smoke test desktop (mở editor, tạo scene 2D/3D, export binary) → Tag `bamboo-v0.1.0-alpha.1`.

---

## 3. Tiêu chí Hoàn thành Sprint (Sprint DoD)
* [ ] C++ Unit Test cho Bamboo Versioning chạy passed 100% qua lệnh `--test`.
* [ ] CI Editor + Export Templates xanh trên cả 3 OS: Windows, macOS, Linux.
* [ ] Đóng gói thành công file `.tpz` export templates cho `0.1.0-alpha.1`.
* [ ] Hoàn thành tài liệu phân tích kỹ thuật và schema mapping cho game Unity3D cần port.
* [ ] Gắn tag git `bamboo-v0.1.0-alpha.1` và phát hành nội bộ.
