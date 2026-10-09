# 🎋 Sprint Coordination: Bamboo 0.1.0-beta.1 (W7 – W8)

> **Mục tiêu Sprint**: Thực chiến Dogfooding game nội bộ trên cả PC & Android, tổ chức Bug Bash toàn công ty, công bố báo cáo đối chuẩn Unity vs Bamboo, và thực hiện Feature Freeze 0.1.  
> **Thời gian**: 23/11/2026 – 04/12/2026  
> **Mốc phát hành**: **`Bamboo 0.1.0-beta.1`** (Cuối W8 - 04/12/2026)

---

## 1. Phân công Vai trò & Nhiệm vụ

| Agent | File Prompt | Trách nhiệm chính |
| :---: | :--- | :--- |
| **GAME / PLT** | `PROMPT_GAME_RUN_AND_VALIDATE.md` | Xuất build game dogfood chạy trên PC và thiết bị thật Android, thu thập crash dump & telemetry. |
| **ALL / QA** | `PROMPT_ALL_BUG_BASH_AND_TRIAGE.md` | Tổ chức Bug Bash toàn đội 2 ngày, phân loại lỗi P0–P3, sửa lỗi nóng và thiết lập regression test. |
| **RT / GAME** | `PROMPT_RT_UNITY_PARITY_BENCHMARK.md` | Đo đạc và lập báo cáo đối chuẩn hiệu năng chi tiết giữa bản gốc Unity3D và bản port Bamboo. |
| **TL** | `PROMPT_TL_FEATURE_FREEZE.md` | Thực hiện **Feature Freeze**, tạo nhánh `release/0.1`, đóng băng API và ban hành chính sách cherry-pick. |

---

## 2. Luồng Phối hợp (Handoff Workflow)

```
       ┌────────────────────────────────────────────────────────┐
       │             Kế thừa từ 0.1.0-alpha.3                   │
       └──────────────────────────┬─────────────────────────────┘
                                  │
    ┌─────────────────────────────┴─────────────────────────────┐
    ▼                                                           ▼
[GAME/PLT: Chạy PC + Android]               [RT: Benchmark Parity Unity vs Bamboo]
    │                                                           │
    └─────────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
                    [ALL: Bug Bash Toàn Đội 2 Ngày]
                                  │
                                  ▼
                   [TL: Feature Freeze & release/0.1]
                                  │
                                  ▼
                     [TAG: bamboo-v0.1.0-beta.1]
```

1. **GAME & PLT Agent**: Export game ra file `.apk` cài lên thiết bị Android tầm trung và bản desktop PC; kiểm tra toàn bộ luồng gameplay.
2. **RT Agent**: Đo đạc chỉ số FPS, draw call, RAM usage, startup time và so sánh trực tiếp với bản build gốc từ Unity3D.
3. **ALL Agents (Bug Bash)**: Đội ngũ tập trung săn lỗi, phân loại issue; các lỗi P0/P1 được sửa ngay và bổ sung unit test chặn tái phát.
4. **TL Agent**: Cắt nhánh `release/0.1`, đóng băng tính năng, chỉ cho phép merge bugfix. Gắn tag `bamboo-v0.1.0-beta.1`.

---

## 3. Tiêu chí Hoàn thành Sprint (Sprint DoD)
* [ ] Game nội bộ port từ Unity3D chạy mượt mà (>= 50–60 FPS) trên cả PC và thiết bị Android thật.
* [ ] Báo cáo đối chuẩn Unity vs Bamboo hoàn tất với số liệu đo đạc thực tế.
* [ ] Nhánh `release/0.1` được khởi tạo thành công; đóng băng 100% tính năng mới.
* [ ] Toàn bộ bug phát hiện trong Bug Bash được gán nhãn P0–P3 và có kế hoạch xử lý dứt điểm ở Sprint 5.
* [ ] Gắn tag git `bamboo-v0.1.0-beta.1`.
