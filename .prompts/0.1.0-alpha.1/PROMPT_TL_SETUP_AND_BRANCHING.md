# TASK [TL]: Khởi Động Dự Án, Chiến Lược Nhánh & Chuẩn Hóa Môi Trường Build

> **Agent**: `TL` (Tech Lead / Orchestrator)  
> **Milestone**: `0.1.0-alpha.1` (Tuần 1 · 12/10 – 16/10/2026)  
> **Mục tiêu**: Chuẩn hóa chiến lược nhánh Git, thiết lập quy chuẩn commit, bảng nhãn Triage issue P0–P3, và tạo script kiểm tra môi trường dev tự động (kèm Unit Test môi trường).

---

## 1. Bối cảnh & Tech Stack
Dự án Bamboo Engine là một fork độc lập từ Godot 4.8.dev (@ commit `c24bf5d933`).
Để đảm bảo quá trình phát triển đa tác tử và rebase upstream sau này không bị xung đột, Tech Lead cần:
- Thiết lập chiến lược 3 nhánh chuẩn: `bamboo/main` (nhánh chính phát triển), `upstream/master` (mirror nguyên bản Godot), và quy ước `release/0.1` (tạo ở W8).
- Chuẩn hóa môi trường build: SCons 4.x+, Python 3.9+, Clang (macOS), MSVC 2022 (Windows), GCC/Clang (Linux).
- Thiết lập quy ước comment `// BAMBOO:` cho toàn bộ thay đổi lõi.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Khởi tạo Cấu trúc Nhánh & Git Hooks
1. Kiểm tra remote Git: đảm bảo có remote `origin` trỏ về repo Bamboo nội bộ và `upstream` trỏ về repo Godot chính thức.
2. Thiết lập quy ước commit theo tính năng:
   - Format: `[Bamboo Area] Mô tả ngắn gọn thay đổi` (VD: `[Bamboo Version] Add Sprout 0.1.0 codename`).
   - Mọi commit chạm vào file lõi (`core/`, `servers/`, `scene/`, `main/`) phải kèm comment `// BAMBOO: <lý do>`.

### Bước 2: Thiết lập Script Kiểm Tra Môi Trường Dev (`misc/scripts/check_dev_env.py`)
Tạo script Python kiểm tra tính sẵn sàng của môi trường dev trên máy kỹ sư trước khi biên dịch:
- Kiểm tra phiên bản Python (`>= 3.9`).
- Kiểm tra phiên bản SCons (`scons --version`).
- Kiểm tra compiler C++ khả dụng theo OS (`clang++` trên macOS, `cl.exe` trên Windows, `g++`/`clang++` trên Linux).
- Kiểm tra dung lượng ổ đĩa trống (yêu cầu tối thiểu 20 GB cho build artifacts).
- Kiểm tra các package Python phụ trợ nếu cần (`pytest`, `Pillow`).

### Bước 3: Viết Unit Test Cho Script Môi Trường (`tests/python_build/test_check_dev_env.py`)
Tạo unit test sử dụng `pytest` hoặc `unittest` để đảm bảo `check_dev_env.py`:
- Trả về mã thoát `0` khi các công cụ đạt chuẩn.
- Báo lỗi rõ ràng và gợi ý lệnh cài đặt chính xác khi thiếu SCons hoặc compiler C++.
- Hỗ trợ tham số `--json` để xuất kết quả cho CI pipeline.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy script kiểm tra môi trường dev
python3 misc/scripts/check_dev_env.py

# 2. Chạy unit test kiểm tra script môi trường
python3 -m unittest discover -s tests/python_build -p "test_*.py"

# 3. Thử nghiệm lệnh build dry-run của SCons
scons platform=macos target=editor -n
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Script `misc/scripts/check_dev_env.py` chạy thành công trên máy dev hiện tại và in ra báo cáo màu xanh lá.
2. File test `tests/python_build/test_check_dev_env.py` pass 100%.
3. Tài liệu [docs/Guides.md](file:///Users/khuyennguyen/Projects/Bamboo/bamboo/docs/Guides.md) được cập nhật danh mục checklist onboarding cho kỹ sư mới.
4. Bảng Kanban/Issue triage có đầy đủ nhãn: `P0-Blocker`, `P1-High`, `P2-Normal`, `P3-Low`, `area/core`, `area/editor`, `area/unity-port`.
