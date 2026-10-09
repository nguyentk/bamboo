# TASK [ALL]: Tổ Chức Bug Bash Toàn Đội 2 Ngày, Phân Loại Triage P0–P3 & Viết Regression Tests

> **Agent**: `ALL` (Toàn bộ các Agent & QA)  
> **Milestone**: `0.1.0-beta.1` (Tuần 8 · 30/11 – 04/12/2026)  
> **Mục tiêu**: Thực hiện đợt Bug Bash toàn diện kéo dài 2 ngày trên mọi nền tảng, phân loại lỗi theo mức độ ưu tiên P0–P3, sửa nóng các lỗi blocker và viết C++ Unit Test (regression test) để ngăn lỗi tái phát.

---

## 1. Bối cảnh & Nguyên Tắc Triage
Trước khi chốt Feature Freeze và phát hành bản Beta.1, toàn bộ đội ngũ kỹ sư và QA dừng phát triển tính năng mới để tập trung kiểm thử phá hủy (destructive testing):
- **Phân loại độ ưu tiên**:
  - `P0 - Blocker`: Crash engine, crash khi export, hỏng file project `.godot`/`.tscn`, rò rỉ bộ nhớ nghiêm trọng. $\rightarrow$ Bắt buộc sửa ngay lập tức, không được phép phát hành nếu còn 1 lỗi P0.
  - `P1 - High`: Tính năng chính bị lỗi nhưng có workaround tạm thời. $\rightarrow$ Sửa trong Sprint 5.
  - `P2 - Normal`: Lỗi giao diện nhỏ, thông báo log chưa chuẩn, lỗi biên (edge case). $\rightarrow$ Chuyển sang Q1/2027.
  - `P3 - Low`: Cải tiến nhỏ (enhancement/polish). $\rightarrow$ Backlog.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Danh Mục Kịch Bản Kiểm Thử Bug Bash
Mỗi Agent phụ trách một khu vực kiểm thử chuyên sâu:
1. **Editor & UI (TLS)**: Tạo project mới, đổi tên file, import tài nguyên lớn, kéo thả node, kiểm tra About dialog và thanh trạng thái phiên bản.
2. **Build & Platform (BQ, PLT)**: Export game ra 6 nền tảng (Win, Mac, Linux, Android, iOS, Web), kiểm tra việc nạp template `.tpz`.
3. **Physics & Runtime (RT)**: Tạo 1.000 vật thể va chạm Jolt liên tục, kiểm tra raycast xuyên tường, kiểm tra signal `body_entered`.
4. **Rendering (RND)**: Đổi qua lại giữa Forward+, Mobile và Compatibility trên các scene phức tạp, kiểm tra shader stuttering.
5. **Dogfood Game (GAME)**: Chơi qua toàn bộ màn chơi của game dogfood trên Android và PC, ghi nhận mọi hiện tượng sụt giảm FPS.

### Bước 2: Quy Trình Sửa Lỗi & Viết Regression Test
Với mỗi lỗi `P0` hoặc `P1` được sửa chữa:
- **Nguyên tắc bắt buộc**: Không chỉ sửa code mà phải viết kèm ít nhất 1 C++ doctest hoặc GDScript test tái hiện chính xác lỗi đó trước khi sửa.
- Tạo test tại `tests/regression/test_issue_<id>.cpp`:
  ```cpp
  #include "tests/test_macros.h"

  TEST_FORCE_LINK(test_regression_issue_102)

  TEST_CASE("[Regression] Issue 102: Crash when reloading project with custom build profile") {
      // Giả lập tình huống gây crash trước đây
      // Assert rằng engine xử lý an toàn và không crash
      CHECK(true);
  }
  ```

### Bước 3: Đăng Ký Test Regression Vào Build System (`tests/SCsub`)
- Đảm bảo toàn bộ test regression được liên kết và chạy tự động trên CI.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy toàn bộ bộ test regression sau khi sửa lỗi
bin/bamboo.macos.editor.arm64 --test --test-case="*[Regression]*"

# 2. Kiểm tra danh sách issue P0 còn mở trên kho lưu trữ
python3 misc/scripts/check_open_issues.py --priority P0
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Danh sách issue của đợt Bug Bash được phân loại 100% với nhãn P0–P3.
2. 100% lỗi P0 phát hiện trong đợt Bug Bash được sửa dứt điểm và merge vào nhánh `release/0.1`.
3. Mọi bản sửa lỗi đều có kèm file unit test regression tương ứng.
4. Toàn bộ test suite `bin/bamboo.* --test` chạy pass 100%.
