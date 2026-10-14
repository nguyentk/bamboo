# Biên bản diễn tập rebase upstream — W5 (thực hiện 12/10/2026)

> Sprint `0.1.0-alpha.3` · TL. Công cụ: `git`, [`misc/scripts/audit_bamboo_patches.py`](../../misc/scripts/audit_bamboo_patches.py).

## 1. Thiết lập

| Mục | Giá trị |
| :--- | :--- |
| Base fork | `c24bf5d933` (Godot `master`, 4.8-dev) |
| Upstream | `upstream/master` = `232e6b14ab` (`https://github.com/godotengine/godot.git`, push bị chặn: `DISABLE`) |
| Commit upstream mới kể từ fork | **659** |
| Commit Bamboo được rebase | **8** (nhánh `develop`, phần đã commit) |
| Nhánh thử | `test-rebase-20261012`, chạy trong `git worktree` riêng (không ảnh hưởng thư mục làm việc) |
| Thời gian `git fetch upstream master` | 12 giây (chỉ tải phần chênh lệch vì base fork nằm trong lịch sử upstream) |

## 2. Kết quả

| Bước | Kết quả |
| :--- | :--- |
| Commit 1–4 (tài liệu `docs/`) | Áp sạch |
| Commit 5 "Thay đổi tên Godot qua Bamboo" | **2 xung đột**, các file khác auto-merge |
| Commit 6–8 (tài liệu, versioning, prompts) | Áp sạch |
| Thời gian máy chạy rebase | ~2 giây đến xung đột đầu, ~1 giây để hoàn tất sau khi giải quyết |
| Thời gian giải quyết xung đột (người) | Vài phút — cả 2 xung đột là cùng dòng, ý nghĩa rõ ràng |

### Chi tiết xung đột

| File | Thay đổi upstream | Thay đổi Bamboo | Cách giải quyết |
| :--- | :--- | :--- | :--- |
| `editor/settings/editor_feature_profile.cpp` (2 chỗ) | `TTR(...)` → `TTRC(...)` cho bộ lọc file `*.profile` | Đổi chuỗi "Godot Feature Profile" → "Bamboo Feature Profile" | Giữ cả hai: `TTRC("Bamboo Feature Profile")` |
| `methods.py` (`generate_vs_project`) | Viết lại `properties.append(...)` sang f-string | Đổi đường dẫn binary `bin/godot…` → `bin/{env.binary_prefix}…` (dòng kế bên) | Giữ f-string của upstream + dòng `binary_prefix` của Bamboo |

Kiểm tra sau khi giải quyết: không còn marker xung đột, `methods.py` parse được (`ast`), chuỗi Bamboo đúng chỗ.

### Thay đổi chưa commit (công việc sprint hiện tại)

`git apply --check --3way` toàn bộ thay đổi chưa commit lên nhánh đã rebase: **3 file sẽ xung đột** — `.github/workflows/web_builds.yml`, `editor/settings/editor_feature_profile.cpp`, `methods.py` — đúng các vùng upstream vừa sửa. Mức độ nhỏ, dự đoán được.

## 3. Kiểm kê patch lõi

Báo cáo đầy đủ: [patch_audit_w5.md](patch_audit_w5.md). Trước diễn tập, chỉ **22/79 patch (27.8%)** có `BAMBOO:` (phần rebranding Phase 2–3 làm trước khi có quy ước). Sau khi bổ sung tag: **100%**.

## 4. Sự cố trong quá trình gắn tag

Khi chèn tag tự động, một dòng `# BAMBOO:` rơi vào **bên trong chuỗi template** của `core/core_builders.py`, sinh ra dòng tiền xử lý không hợp lệ trong `core/version_generated.gen.h` và làm hỏng bản build iOS simulator đang chạy song song. Đã sửa bằng comment C (`// BAMBOO:`) hợp lệ trong header sinh ra, và thêm test hồi quy `BAMBOO-REG-1` (`tests/python_build/test_regression_version_header.py`, `tests/regression/test_regression_version_header.cpp`).

## 5. Bài học & đề xuất

1. **Rebase thường xuyên**: 659 commit upstream chỉ gây 2 xung đột vì patch Bamboo nhỏ và tập trung. Đề xuất rebase mỗi 2 tuần (mỗi sprint) thay vì mỗi bản minor.
2. **Giữ patch chuỗi/tên file trong commit riêng**: toàn bộ xung đột đến từ commit rebranding — nơi upstream cũng hay sửa (`TTR`→`TTRC`, refactor Python).
3. **Không tự động chèn tag vào file sinh code** (template trong Python): luôn xem ngữ cảnh; `audit_bamboo_patches.py` chỉ báo cáo, việc chèn tag làm thủ công hoặc có review.
4. **Không chạy hai bản build SCons song song** trong cùng thư mục (dùng chung `.sconsign.dblite` và file sinh ra).
5. CI nên chạy `audit_bamboo_patches.py` cho mỗi PR để giữ 100% patch có tag.

## 6. Dọn dẹp

Nhánh thử `test-rebase-20261012` và worktree tạm là của buổi diễn tập; nhánh làm việc chính (`develop`) không bị rebase.
