# 🎋 Sprint Coordination: Bamboo 0.1.0-alpha.3 (W5 – W6)

> **Mục tiêu Sprint**: Diễn tập Rebase Upstream Godot master, kích hoạt Jolt Physics 3D làm mặc định, xây dựng 3 Build Profiles tối ưu kích thước binary, và hoàn thiện port logic/scene của game Unity3D.  
> **Thời gian**: 09/11/2026 – 20/11/2026  
> **Mốc phát hành**: **`Bamboo 0.1.0-alpha.3`** (Cuối W6 - 20/11/2026)

---

## 1. Phân công Vai trò & Nhiệm vụ

| Agent | File Prompt | Trách nhiệm chính |
| :---: | :--- | :--- |
| **TL** | `PROMPT_TL_UPSTREAM_REBASE_REHEARSAL.md` | Viết script kiểm kê patch `// BAMBOO:`, thực hiện diễn tập rebase Godot master, dựng repo `bamboo_modules`. |
| **RT** | `PROMPT_RT_JOLT_DEFAULT_AND_TESTS.md` | Bật Jolt Physics làm mặc định cho project mới, xử lý migration project cũ, **viết C++ doctest**. |
| **BQ / PLT** | `PROMPT_BQ_BUILD_PROFILES.md` | Xây dựng 3 profile SCons (`bamboo_2d`, `bamboo_mobile`, `bamboo_pc`), đo đạc dung lượng binary & test. |
| **GAME / RT** | `PROMPT_GAME_UNITY_LOGIC_AND_SCENE.md` | Chuyển đổi logic script từ MonoBehaviour sang Bamboo, ghép scene hoàn chỉnh và cấu hình Jolt physics. |

---

## 2. Luồng Phối hợp (Handoff Workflow)

```
       ┌────────────────────────────────────────────────────────┐
       │             Kế thừa từ 0.1.0-alpha.2                   │
       └──────────────────────────┬─────────────────────────────┘
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    ▼                             ▼                             ▼
[TL: Rebase & bamboo_modules]  [RT: Jolt Physics Default]   [BQ: Build Profiles]
    │                             │                             │
    └──────────────────────┬──────┴─────────────────────────────┘
                           │
                           ▼
          [GAME: Ghép Scene & Logic Porting]
                           │
                           ▼
              [TAG: bamboo-v0.1.0-alpha.3]
```

1. **TL Agent**: Kiểm kê 100% patch lõi có nhãn `// BAMBOO:`, tạo nhánh thử nghiệm và diễn tập rebase lên `upstream/master`, ghi chép thời gian và xung đột vào báo cáo rebase.
2. **RT Agent**: Sửa cài đặt mặc định trong `project_settings.cpp` để Jolt 3D Physics là backend chuẩn; viết C++ unit test kiểm tra tạo RigidBody3D và va chạm mô phỏng.
3. **BQ Agent**: Viết 3 file cấu hình build profile, kiểm tra biên dịch binary và đo đạc mức giảm dung lượng binary.
4. **GAME Agent**: Tận dụng Jolt Physics mặc định và các model đã convert ở W4 để ráp scene hoàn chỉnh, viết lại logic điều khiển người chơi sang script Bamboo.
5. **Hợp nhất**: Đóng gói bản build `0.1.0-alpha.3`.

---

## 3. Tiêu chí Hoàn thành Sprint (Sprint DoD)
* [ ] Hoàn thành 1 lần diễn tập rebase lên Godot master với báo cáo giải quyết xung đột chi tiết.
* [ ] C++ Unit Test cho Jolt Physics mặc định pass 100%.
* [ ] 3 Build profile (`2d`, `mobile`, `pc`) biên dịch thành công và giảm được ít nhất 20–35% dung lượng binary cho bản 2D/Mobile.
* [ ] Game Unity nội bộ đã ghép xong scene chính và chạy thử được các cơ chế gameplay cơ bản trên Bamboo.
* [ ] Gắn tag git `bamboo-v0.1.0-alpha.3`.
