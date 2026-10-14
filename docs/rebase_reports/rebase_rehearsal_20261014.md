# Biên bản diễn tập rebase upstream — lần 2 (thực hiện 14/10/2026, sprint `0.1.0-alpha.3`)

> TL. Lần 1: [rebase_rehearsal_w5.md](rebase_rehearsal_w5.md) (12/10/2026). Lần này rebase **toàn bộ** công việc Bamboo,
> kể cả phần chưa commit, và build + chạy test trên kết quả.

## 1. Thiết lập

| Mục | Giá trị |
| :--- | :--- |
| Base fork | `c24bf5d933` (Godot `master`, 4.8-dev) |
| Upstream | `upstream/master` = `5ec712e220` — **743** commit mới kể từ fork (lần 1: 659, +84 trong 2 ngày) |
| Thời gian `git fetch upstream master` | 6 giây |
| Nội dung rebase | 8 commit của nhánh `develop` + 1 commit snapshot chứa toàn bộ thay đổi chưa commit (162 file, ~39 000 dòng thêm) |
| Cách chụp snapshot | `git read-tree` / `git add -A` / `git write-tree` / `git commit-tree` với `GIT_INDEX_FILE` tạm — không đụng thư mục làm việc và index thật |
| Nơi thực hiện | nhánh `test-rebase-20261014` trong `git worktree` riêng |

## 2. Kết quả

| Bước | Kết quả | Thời gian |
| :--- | :--- | ---: |
| Commit 1–4 (tài liệu) | Áp sạch | |
| Commit 5 "Thay đổi tên Godot qua Bamboo" | 2 xung đột (giống lần 1) | máy 3 s |
| Commit 6–8 | Áp sạch | |
| Commit snapshot (công việc chưa commit) | 3 xung đột | máy 1 s |
| Giải quyết xung đột | 5 khối, theo quy tắc cố định (bên dưới) | vài phút |
| `make_pot.py` (chuỗi upstream thay đổi) | 6 641 → 6 709 msgid, `msgfmt --check` OK | 2 s |
| Build editor macOS arm64 (`tests=yes`, build sạch) | Thành công | 459 s |
| C++ doctest | **1445/1445 pass** (upstream thêm 9 test case) | |
| `[BambooVersion]`, `[JoltPhysics]`, `[Regression]` | 9/9 pass | |
| Test Python (`tests/python_build`) | 205 pass, 12 skip (không có binary/release dir trong worktree) | |
| Audit patch (`--base upstream/master`) | 48 file chạm (22 mới), **93/93 patch có tag** | |

### Chi tiết xung đột

| File | Upstream thay đổi | Bamboo thay đổi | Giải quyết |
| :--- | :--- | :--- | :--- |
| `editor/settings/editor_feature_profile.cpp` (2 chỗ, cả 2 commit) | `TTR` → `TTRC` | "Godot Feature Profile" → "Bamboo Feature Profile" + comment `// BAMBOO:` | `TTRC("Bamboo Feature Profile")` + giữ comment |
| `methods.py` (cả 2 commit) | `properties.append(...)` viết lại bằng f-string | dòng `binary_prefix` + comment `# BAMBOO:` ngay bên dưới | f-string của upstream + dòng/comment Bamboo |
| `.github/workflows/web_builds.yml` | `EM_VERSION` 6.0.1 → **6.0.12** | thêm `engine_update_check=no` vào `SCONS_FLAGS` (dòng kề) | Giữ cả hai: Emscripten 6.0.12 + cờ Bamboo |

Toàn bộ xung đột là **xung đột dòng kề** (hai bên sửa các dòng sát nhau), không có xung đột ngữ nghĩa.

## 3. Sự cố khi kiểm tra

Lần chạy test đầu tiên trên bản rebase báo 1 test GDScript lỗi (`typed_array.gd`, `typed_dictionary.gd`). Nguyên nhân: binary
được chạy từ **thư mục làm việc chính**, nên test runner GDScript đọc script/`.out` của cây cũ (đường dẫn tương đối theo thư
mục hiện tại). Chạy lại từ trong worktree: 1445/1445 pass. → Khi kiểm tra một cây khác, luôn `cd` vào cây đó trước khi chạy `--test`.

## 4. Đánh giá & đề xuất

1. **Rủi ro rebase thấp**: 743 commit upstream, 5 khối xung đột, tất cả có quy tắc giải quyết lặp lại được. Đề xuất giữ lịch rebase mỗi sprint (2 tuần).
2. **Cùng 2 file xung đột ở cả 2 lần** (`editor_feature_profile.cpp`, `methods.py`): khi commit phần chưa commit, nên **gộp** thay đổi
   rebranding và tag `BAMBOO:` của 2 file này vào một commit để chỉ phải giải quyết một lần.
3. Sau mỗi rebase phải chạy lại `misc/scripts/make_pot.py` (test `.pot` sẽ báo lỗi nếu quên).
4. Upstream đã nâng Emscripten lên 6.0.12 — `docs/Guides.md` và `check_dev_env.py` nên cập nhật khi rebase thật.
5. Commit phần công việc đang chưa commit sớm: snapshot hiện chứa 162 file; càng để lâu, rebase thật càng khó review.

## 5. Dọn dẹp

Nhánh `test-rebase-20261014` và worktree tạm đã xóa sau buổi diễn tập; nhánh `develop` và thư mục làm việc không bị thay đổi.
