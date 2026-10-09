# TASK [TL]: Thiết Lập Nhánh release/0.1, Đóng Băng Tính Năng (Feature Freeze) & Release Beta.1

> **Agent**: `TL` (Tech Lead / Orchestrator)  
> **Milestone**: `0.1.0-beta.1` (Tuần 8 · 30/11 – 04/12/2026)  
> **Mục tiêu**: Thực hiện thủ tục Feature Freeze cho phiên bản 0.1; tạo nhánh bảo trì `release/0.1`; nâng phiên bản lên `0.1.0-beta.1`; thiết lập chính sách cherry-pick và viết unit test kiểm tra trạng thái freeze.

---

## 1. Bối cảnh & Chính Sách Feature Freeze
Sau tuần 8, toàn bộ tính năng mới dự kiến cho Bamboo 0.1.0 "Sprout" phải được đóng băng (Feature Freeze):
- Không chấp nhận thêm bất kỳ tính năng mới, thay đổi API hay refactor lớn nào vào nhánh release.
- Tạo nhánh riêng `release/0.1` dành riêng cho việc sửa lỗi và ổn định hóa trong 2 tuần tiếp theo (Sprint 5).
- Mọi bản sửa lỗi phải được commit trên nhánh `release/0.1` trước, sau đó cherry-pick về `bamboo/main`.
- Đổi trường `bamboo_prerelease = "beta.1"` trong `version.py`.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Khởi Tạo Nhánh Release & Cập Nhật Versioning
1. Tạo nhánh phát hành:
   ```bash
   git checkout bamboo/main
   git pull origin bamboo/main
   git checkout -b release/0.1
   ```
2. Cập nhật file `version.py`:
   ```python
   # BAMBOO: Bamboo product version
   bamboo_major = 0
   bamboo_minor = 1
   bamboo_patch = 0
   bamboo_prerelease = "beta.1"
   bamboo_codename = "Sprout"
   ```
3. Commit với thông điệp: `[Bamboo Release] Bump version to 0.1.0-beta.1 and establish release/0.1 branch`.

### Bước 2: Thiết Lập Chính Sách Cherry-Pick & CI Bảo Vệ Nhánh
1. Tạo tài liệu hướng dẫn: `docs/policies/release_freeze_policy.md`.
2. Cấu hình branch protection rule trên GitHub:
   - Yêu cầu mọi PR vào `release/0.1` phải có ít nhất 1 review từ Tech Lead (`TL`).
   - Yêu cầu toàn bộ test CI (Desktop, Mobile, Web) phải xanh trước khi merge.

### Bước 3: Viết Script Kiểm Tra Tính Hợp Lệ Của Nhánh Release (`misc/scripts/check_release_branch.py`)
Script Python kiểm tra:
- Đảm bảo nhánh hiện tại đang ở đúng quy ước `release/0.x`.
- Đảm bảo `version.py` có `bamboo_prerelease` chứa chuỗi `beta` hoặc `rc`.
- Quét commit log để cảnh báo nếu có commit chứa từ khóa `feat:` hoặc `feature:` thay vì `fix:`.

### Bước 4: Viết Unit Test Kiểm Tra Trạng Thái Freeze (`tests/python_build/test_release_freeze.py`)
Tạo unit test Python:
- Kiểm tra các biến phiên bản trong `version.py` khớp với trạng thái Beta.1.
- Kiểm tra logic của script kiểm tra nhánh release hoạt động đúng với các kịch bản test giả lập.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm tra trạng thái freeze
python3 -m unittest tests/python_build/test_release_freeze.py

# 2. Chạy script kiểm tra nhánh release
python3 misc/scripts/check_release_branch.py --branch release/0.1

# 3. Biên dịch và kiểm tra phiên bản Beta hiển thị trong terminal
scons platform=macos target=editor tests=yes dev_build=yes -j$(nproc)
bin/bamboo.macos.editor.arm64 --version
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Nhánh `release/0.1` được đẩy lên remote Git thành công.
2. File `version.py` được cập nhật thành `0.1.0-beta.1`.
3. File test `tests/python_build/test_release_freeze.py` pass 100%.
4. Gắn git tag `bamboo-v0.1.0-beta.1` và phát hành bản build Beta.1 nội bộ.
