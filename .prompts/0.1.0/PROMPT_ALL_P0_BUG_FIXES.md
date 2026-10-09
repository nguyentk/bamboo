# TASK [ALL]: Triệt Tiêu 100% Lỗi P0/P1 Còn Mở & Xác Thực Toàn Diện Regression Suite

> **Agent**: `ALL` (Toàn bộ các Agent & QA)  
> **Milestone**: `0.1.0` (Tuần 9 · 07/12 – 11/12/2026)  
> **Mục tiêu**: Tập trung toàn lực sửa dứt điểm mọi lỗi P0 (Blocker) và P1 (High) còn mở trên nhánh `release/0.1`; đảm bảo không phát sinh lỗi mới thông qua bộ test hồi quy toàn diện.

---

## 1. Bối cảnh & Tiêu Chuẩn Chất Lượng
Theo kế hoạch chất lượng Q4/2026:
- **Tiêu chí sống còn**: `0 lỗi P0 mở tại thời điểm phát hành 18/12`.
- Mọi bản vá lỗi (hotfix/patch) trong tuần W9 phải được kiểm thử chéo (cross-tested) trên cả 3 hệ điều hành desktop và 2 hệ điều hành di động.
- Không cho phép merge bất kỳ đoạn code nào nếu chưa có unit test hồi quy đi kèm.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Rà Soát & Đốt Cháy Backlog Lỗi (Bug Burn-down)
1. Liệt kê danh sách toàn bộ bug P0/P1 còn mở:
   ```bash
   python3 misc/scripts/check_open_issues.py --priority P0,P1
   ```
2. Phân công trực tiếp cho các Agent chuyên trách:
   - Crash render / driver Vulkan $\rightarrow$ `RND Agent`.
   - Lỗi Jolt Physics va chạm / xuyên thấu $\rightarrow$ `RT Agent`.
   - Lỗi export Android / iOS $\rightarrow$ `PLT Agent`.
   - Lỗi UI / Scene corruption $\rightarrow$ `TLS Agent`.

### Bước 2: Kiểm Thử Hồi Quy Toàn Diện (Full Regression Run)
Sau khi các bản vá được merge vào `release/0.1`:
1. Chạy toàn bộ các test case có sẵn của Godot/Bamboo:
   ```bash
   bin/bamboo.macos.editor.arm64 --test
   ```
2. Chạy toàn bộ bộ test hồi quy riêng:
   ```bash
   bin/bamboo.macos.editor.arm64 --test --test-case="*[Regression]*"
   ```
3. Chạy lại bộ benchmark suite để xác nhận không bị suy giảm hiệu năng:
   ```bash
   python3 misc/scripts/run_benchmarks.py --binary bin/bamboo.macos.editor.arm64
   ```

### Bước 3: Viết Unit Test Kiểm Tra Đóng Sạch Bug P0 (`tests/python_build/test_zero_p0_verification.py`)
Tạo script test tự động kiểm tra trạng thái issue:
- Kiểm tra danh sách issue P0 mở trả về danh sách rỗng (`[]`).
- Đảm bảo toàn bộ commit trên nhánh `release/0.1` đều có ticket ID tham chiếu hợp lệ.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test xác thực không còn lỗi P0 mở
python3 -m unittest tests/python_build/test_zero_p0_verification.py

# 2. Chạy toàn bộ C++ test suite với doctest
bin/bamboo.macos.editor.arm64 --test
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Số lượng lỗi P0 mở bằng đúng **0**.
2. Toàn bộ C++ unit tests trong `bin/bamboo.* --test` chạy thành công 100% không có failure nào.
3. Bộ benchmark nightly xác nhận chỉ số FPS và RAM không sụt giảm quá 1% so với bản Beta.1.
