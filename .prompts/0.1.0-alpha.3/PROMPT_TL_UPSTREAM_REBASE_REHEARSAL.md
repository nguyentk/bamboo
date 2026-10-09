# TASK [TL]: Diễn Tập Rebase Upstream, Kiểm Kê Patch // BAMBOO: & Repo bamboo_modules

> **Agent**: `TL` (Tech Lead / Orchestrator)  
> **Milestone**: `0.1.0-alpha.3` (Tuần 5 · 09/11 – 13/11/2026)  
> **Mục tiêu**: Xây dựng script kiểm kê patch lõi `// BAMBOO:`, thực hiện diễn tập rebase lên nhánh Godot master mới nhất trên nhánh thử nghiệm, thiết lập cơ chế nạp module mở rộng `bamboo_modules`, và viết unit test kiểm tra công cụ audit.

---

## 1. Bối cảnh & Tech Stack
Là một engine fork, nguy cơ lớn nhất khi phát triển lâu dài là **"lệch xa upstream" (divergence)**, dẫn đến việc rebase hoặc cherry-pick tính năng mới/bảo mật từ Godot trở nên bất khả thi do xung đột mã nguồn khổng lồ.
Chiến lược kỹ thuật của Bamboo Engine để giải quyết rủi ro này gồm 3 trụ cột:
1. **Quy tắc 100% Patch lõi**: Bất kỳ thay đổi nào trong `core/`, `servers/`, `scene/`, `editor/` bắt buộc phải được đánh dấu bằng tag `// BAMBOO:`.
2. **Kiến trúc Module Độc Lập**: Mọi tính năng mở rộng mới không sửa trực tiếp vào repo chính mà đưa vào thư mục module nạp qua `custom_modules=bamboo_modules`.
3. **Diễn tập Rebase Định kỳ**: Thực hiện rebase thử nghiệm trên nhánh clone, đo thời gian xử lý và lưu nhật ký xung đột.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Viết Script Kiểm Kê Patch Lõi (`misc/scripts/audit_bamboo_patches.py`)
Script Python quét toàn bộ cây mã nguồn (loại trừ `thirdparty/` và `.git/`):
- Tìm kiếm các commit khác biệt giữa `bamboo/main` và `upstream/master`.
- Quét các dòng code đã sửa đổi, kiểm tra xem có xuất hiện comment `// BAMBOO:` hay không.
- Xuất báo cáo dạng Markdown: tổng số file bị chạm, tổng số patch, số dòng code thay đổi và danh sách các file thiếu nhãn `// BAMBOO:`.

### Bước 2: Thiết Lập Thư Mục `bamboo_modules` & Module Mẫu `bamboo_core`
1. Tạo thư mục cấu trúc module ngoài:
   ```
   bamboo_modules/
   └── bamboo_core/
       ├── config.py
       ├── register_types.h
       ├── register_types.cpp
       └── SCsub
   ```
2. Thử nghiệm biên dịch với cờ SCons:
   ```bash
   scons platform=macos target=editor custom_modules=bamboo_modules dev_build=yes -j$(nproc)
   ```

### Bước 3: Thực Hiện Diễn Tập Rebase Trên Nhánh Thử Nghiệm
1. Tạo nhánh thử nghiệm:
   ```bash
   git checkout -b test-rebase-$(date +%Y%m%d)
   git fetch upstream
   git rebase upstream/master
   ```
2. Ghi lại:
   - Các file bị conflict (nếu có).
   - Thời gian giải quyết conflict.
   - Biên bản đúc kết tại `docs/rebase_reports/rebase_rehearsal_w5.md`.

### Bước 4: Viết Unit Test Kiểm Tra Script Audit (`tests/python_build/test_patch_auditor.py`)
Tạo unit test Python kiểm tra:
- Phát hiện chính xác khối code có chứa comment `// BAMBOO:`.
- Cảnh báo lỗi exit code non-zero khi phát hiện diff không có nhãn.
- Khả năng bỏ qua đúng các file trong `thirdparty/`.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm chứng script audit patch
python3 -m unittest tests/python_build/test_patch_auditor.py

# 2. Chạy audit trên toàn bộ repository hiện tại
python3 misc/scripts/audit_bamboo_patches.py --output docs/rebase_reports/patch_audit_w5.md

# 3. Kiểm tra biên dịch kèm custom module
scons platform=macos target=editor custom_modules=bamboo_modules dev_build=yes -n
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Báo cáo audit xác nhận 100% thay đổi của Bamboo Engine có gắn nhãn `// BAMBOO:`.
2. File test `tests/python_build/test_patch_auditor.py` pass 100%.
3. Module mẫu `bamboo_modules/bamboo_core` liên kết thành công vào engine mà không có lỗi linker.
4. Có biên bản diễn tập rebase hoàn chỉnh lưu tại `docs/rebase_reports/rebase_rehearsal_w5.md`.
