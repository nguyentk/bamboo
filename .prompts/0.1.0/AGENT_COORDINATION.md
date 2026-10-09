# 🎋 Sprint Coordination: Bamboo 0.1.0 "Sprout" GA (W9 – W10)

> **Mục tiêu Sprint**: Triệt tiêu 100% bug P0/P1, đóng gói bản phát hành chính thức (.dmg notarized, .zip, .tpz), hoàn thiện tài liệu Migration Guide, tiến hành họp Go/No-go và Phát hành chính thức Bamboo 0.1.0 "Sprout".  
> **Thời gian**: 07/12/2026 – 18/12/2026  
> **Mốc phát hành**:  
> - Ứng viên phát hành: **`Bamboo 0.1.0-rc.1`** (15/12/2026)  
> - Phát hành chính thức: **`Bamboo 0.1.0 "Sprout"`** (18/12/2026)

---

## 1. Phân công Vai trò & Nhiệm vụ

| Agent | File Prompt | Trách nhiệm chính |
| :---: | :--- | :--- |
| **ALL** | `PROMPT_ALL_P0_BUG_FIXES.md` | Tập trung toàn lực giải quyết 100% bug P0 và P1 còn mở; viết regression tests. |
| **BQ** | `PROMPT_BQ_PACKAGING_NOTARIZATION.md` | Đóng gói bản cài đặt: `.dmg` (đã notarize với Apple), `.zip` Windows/Linux, `.tpz` templates. |
| **TLS** | `PROMPT_TLS_LOCALIZATION_AND_DOCS.md` | Cập nhật file ngôn ngữ `.pot`, biên soạn tài liệu Migration Guide "Unity3D to Bamboo Engine". |
| **TL** | `PROMPT_TL_GO_NOGO_AND_RELEASE.md` | Điều phối Go/No-go meeting (17/12), gỡ hậu tố prerelease (`""`), gắn tag release `bamboo-v0.1.0`. |

---

## 2. Luồng Phối hợp (Handoff Workflow)

```
       ┌────────────────────────────────────────────────────────┐
       │             Kế thừa từ 0.1.0-beta.1                    │
       └──────────────────────────┬─────────────────────────────┘
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    ▼                             ▼                             ▼
[ALL: Sửa Triệt Để P0/P1]     [TLS: Docs & Localization]     [BQ: Packaging & Sign]
    │                             │                             │
    └──────────────────────┬──────┴─────────────────────────────┘
                           │
                           ▼
              [MỐC: 0.1.0-rc.1 (15/12/2026)]
                           │
                           ▼
              [TL: Go/No-go Meeting (17/12)]
                           │
                           ▼
          [🚀 PHÁT HÀNH CHÍNH THỨC: 18/12/2026]
              Bamboo 0.1.0 "Sprout" (Nội bộ & Đối tác)
```

1. **W9 (07–11/12)**: Toàn bộ kỹ sư tập trung đóng toàn bộ bug P0/P1 trên nhánh `release/0.1`. BQ hoàn thiện pipeline ký số và notarization. TLS cập nhật tài liệu hướng dẫn migration.
2. **W10 - 15/12**: Cắt bản ứng viên **`0.1.0-rc.1`**. Chạy lại toàn bộ test suite, benchmark nightly và golden image test.
3. **W10 - 17/12**: Tech Lead chủ trì cuộc họp **Go/No-go Meeting**:
   - Nếu còn $\ge 1$ lỗi P0: **NO-GO** (sửa khẩn cấp).
   - Nếu 0 lỗi P0, CI xanh 6/6: **GO**.
4. **W10 - 18/12**: Xóa bỏ `bamboo_prerelease` (thành chuỗi rỗng `""`), build bản chính thức, gắn tag `bamboo-v0.1.0`, xuất bản release notes và demo game nội bộ đã port.

---

## 3. Tiêu chí Hoàn thành Sprint (Sprint DoD)
* [ ] 0 lỗi P0 mở tại thời điểm phát hành (Điều kiện tiên quyết).
* [ ] Gói `.dmg` trên macOS vượt qua kiểm định Apple Notarization (`spctl --assess` pass).
* [ ] Bộ tài liệu "Hướng dẫn chuyển đổi Unity3D sang Bamboo Engine" hoàn tất tại `docs/unity_port/`.
* [ ] Họp Go/No-go thống nhất quyết định GO 100%.
* [ ] Gắn tag git `bamboo-v0.1.0` và công bố bản phát hành chính thức cho nội bộ và đối tác.
