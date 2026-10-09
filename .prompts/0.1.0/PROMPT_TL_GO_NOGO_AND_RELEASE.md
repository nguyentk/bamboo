# TASK [TL]: Điều Phối Go/No-Go Meeting, Tag Release bamboo-v0.1.0 "Sprout" & Công Bố Bản Phát Hành Chính Thức

> **Agent**: `TL` (Tech Lead / Orchestrator)  
> **Milestone**: `0.1.0` (Tuần 10 · 14/12 – 18/12/2026)  
> **Mục tiêu**: Điều phối phát hành ứng viên `0.1.0-rc.1` (15/12); tổ chức cuộc họp Go/No-go (17/12); chuyển phiên bản sang bản chính thức `bamboo_prerelease = ""`; gắn tag `bamboo-v0.1.0`, xuất bản Release Notes và bàn giao cho nội bộ & đối tác (18/12).

---

## 1. Bối cảnh & Quy Trình Phát Hành GA (General Availability)
Tuần W10 là thời khắc cán đích của toàn bộ chiến dịch Q4/2026 ("Nền Móng"):
- **Lịch trình mốc thời gian**:
  - **15/12/2026**: Phát hành ứng viên `0.1.0-rc.1` để chạy lại toàn bộ smoke test, benchmark và golden image test.
  - **17/12/2026**: Họp **Go/No-go Meeting** toàn đội dựa trên checklist nghiệm thu nghiêm ngặt.
  - **18/12/2026**: **PHÁT HÀNH CHÍNH THỨC BAMBOO 0.1.0 "SPROUT"** trước kỳ nghỉ lễ Giáng Sinh và năm mới.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Phát Hành Bản Ứng Viên `0.1.0-rc.1` (15/12)
1. Cập nhật `version.py`:
   ```python
   bamboo_prerelease = "rc.1"
   ```
2. Kích hoạt toàn bộ runner CI build lại toàn bộ matrix và chạy regression suite.

### Bước 2: Checklist Nghiệm Thu Cuộc Họp Go/No-Go (17/12)
Tech Lead kiểm tra 9 tiêu chí điều kiện tiên quyết (Exit Criteria):
- [ ] **Tiêu chí 1**: CI xanh 100% trên cả 6 nền tảng (Win, Mac, Linux, Android, iOS, Web).
- [ ] **Tiêu chí 2**: Số lượng lỗi P0 mở bằng **0**.
- [ ] **Tiêu chí 3**: Kịch bản benchmark nightly có baseline cho $\ge 6$ kịch bản.
- [ ] **Tiêu chí 4**: Golden-image test đạt chuẩn cho 3 renderer (Forward+, Mobile, Compatibility).
- [ ] **Tiêu chí 5**: Thời gian CI build Editor có cache $\le 20$ phút.
- [ ] **Tiêu chí 6**: Game nội bộ port từ Unity3D chạy mượt mà trên PC và Android thật.
- [ ] **Tiêu chí 7**: 100% patch mã nguồn lõi có comment `// BAMBOO:`.
- [ ] **Tiêu chí 8**: Đã diễn tập rebase upstream Godot master ít nhất 1 lần (có biên bản).
- [ ] **Tiêu chí 9**: Gói cài đặt `.dmg` macOS đã được Apple Notarize thành công.

### Bước 3: Đổi Trạng Thái Phiên Bản & Gắn Tag Chính Thức (18/12)
1. Cập nhật `version.py` (chuyển sang bản chính thức, xóa bỏ hậu tố prerelease):
   ```python
   # BAMBOO: Bamboo product version (Stable 0.1.0)
   bamboo_major = 0
   bamboo_minor = 1
   bamboo_patch = 0
   bamboo_prerelease = ""  # Chuỗi rỗng: Đánh dấu bản phát hành chính thức
   bamboo_codename = "Sprout"
   ```
2. Commit và gắn Git Tag:
   ```bash
   git commit -am "[Bamboo Release] Bamboo Engine 0.1.0 'Sprout' Official Release"
   git tag -a bamboo-v0.1.0 -m "Bamboo Engine v0.1.0 'Sprout' GA Release"
   git push origin release/0.1 --tags
   ```

### Bước 4: Viết Release Notes & Unit Test Kiểm Tra Đủ Điều Kiện Release (`tests/python_build/test_release_candidate_readiness.py`)
1. Tạo tài liệu Release Notes tại `docs/release_notes/Release_Notes_0.1.0_Sprout.md`:
   - Lời mở đầu giới thiệu Bamboo Engine 0.1.0 "Sprout".
   - Các tính năng nổi bật: Jolt Physics mặc định, 3 Build Profiles tối ưu dung lượng, Dual-versioning bảo toàn GDExtension ABI.
   - Thành tựu port thành công game Unity3D nội bộ.
   - Hướng dẫn cài đặt và khởi chạy.
2. Viết test Python tự động kiểm tra xem `version.py` đã ở trạng thái stable chưa trước khi tag:
   - `bamboo_prerelease == ""`
   - `bamboo_major == 0`, `bamboo_minor == 1`, `bamboo_patch == 0`
   - Đảm bảo file Release Notes tồn tại và không rỗng.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm tra điều kiện phát hành GA
python3 -m unittest tests/python_build/test_release_candidate_readiness.py

# 2. Kiểm tra tag git đã được tạo
git tag -l "bamboo-v0.1.0"

# 3. Chạy binary bản build cuối cùng kiểm tra hiển thị chuỗi phiên bản
bin/bamboo.macos.editor.arm64 --version
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Quyết định Go/No-go meeting đạt đồng thuận **GO 100%**.
2. Git tag `bamboo-v0.1.0` được tạo và push lên repository chính thức.
3. Bộ phát hành hoàn chỉnh (.dmg, .zip, .tpz) cùng bản demo game đã port từ Unity được công bố nội bộ và đối tác.
4. Tài liệu Release Notes được xuất bản đầy đủ.
