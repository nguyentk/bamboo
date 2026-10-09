# TASK [BQ]: Thiết Lập CI Desktop, Tắt Update Check & Đóng Gói Export Templates .tpz

> **Agent**: `BQ` (Build, CI & QA)  
> **Milestone**: `0.1.0-alpha.1` (Tuần 2 · 19/10 – 23/10/2026)  
> **Mục tiêu**: Hoàn thiện CI build Editor & Templates cho Windows, macOS, Linux với SCons caching; tắt kiểm tra update từ máy chủ Godot; đóng gói export templates offline `.tpz` (kèm Unit Test kiểm tra gói).

---

## 1. Bối cảnh & Tech Stack
- Bamboo Engine có mã nguồn tại repo và các workflow CI tại `.github/workflows/`.
- Bản build Bamboo cần:
  1. `BUILD_NAME=bamboo` (không dùng `official` để tránh các rule mặc định của Godot như bundle id macOS).
  2. Tắt kiểm tra cập nhật từ server Godot (`engine_update_check=no`).
  3. Đóng gói templates debug & release thành file zip nén `.tpz` (tương đương chuẩn Godot `.tpz`) để người dùng có thể cài đặt trực tiếp từ menu Editor (`Project > Install Export Templates...`).
  4. SCons cache (`SCONS_CACHE` / GitHub Cache action) để thời gian build mỗi platform $\le 20$ phút.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Cấu hình Cờ SCons & GitHub Actions Desktop
1. Cập nhật các file:
   - `.github/workflows/linux_builds.yml`
   - `.github/workflows/macos_builds.yml`
   - `.github/workflows/windows_builds.yml`
2. Đảm bảo các tham số build:
   ```bash
   scons platform=<os> target=editor build_name=bamboo engine_update_check=no dev_build=no -j$(nproc)
   scons platform=<os> target=template_release build_name=bamboo engine_update_check=no dev_build=no -j$(nproc)
   scons platform=<os> target=template_debug build_name=bamboo engine_update_check=no dev_build=no -j$(nproc)
   ```
3. Cấu hình GitHub Actions cache cho thư mục cache SCons (`~/.scons_cache/`).

### Bước 2: Viết Script Đóng Gói Export Templates (`misc/scripts/package_templates.py`)
Tạo script Python đóng gói các binary template thành file `.tpz` tương thích cấu trúc thư mục Godot:
- Đọc thông tin phiên bản từ `version.py` (`major.minor` của Godot + `bamboo_string`).
- Tạo cấu trúc thư mục bên trong zip: `templates/<godot_version_full_name>/`.
- Gom các binary:
  - Windows: `windows_debug_x86_64.exe`, `windows_release_x86_64.exe`
  - Linux: `linux_debug_x86_64`, `linux_release_x86_64`
  - macOS: `macos.zip` (chứa binary Universal/arm64)
- Ghi kèm file `version.txt` bên trong gói `.tpz`.

### Bước 3: Viết Unit Test Kiểm Tra Đóng Gói (`tests/python_build/test_package_templates.py`)
Tạo unit test kiểm tra tính toàn vẹn của file `.tpz`:
- Kiểm tra file sinh ra là file zip hợp lệ.
- Kiểm tra sự tồn tại của thư mục gốc `templates/` bên trong zip.
- Kiểm tra nội dung file `version.txt` khớp với chuỗi phiên bản từ `version.py`.
- Kiểm tra cơ chế xử lý khi thiếu binary đầu vào (phải đưa ra cảnh báo rõ ràng thay vì crash unhandled).

### Bước 4: Viết Kịch Bản Smoke Test Tự Động (`misc/scripts/smoke_test.py`)
Tạo script kiểm tra nhanh binary sau khi build:
- Chạy binary editor ở chế độ headless: `bin/bamboo.* --headless --quit`.
- Kiểm tra mã thoát (phải bằng 0).
- Kiểm tra output log có chứa chuỗi `Bamboo Engine v0.1.0-alpha.1 (Godot 4.8.dev.custom_build)`.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy unit test kiểm tra logic đóng gói templates
python3 -m unittest tests/python_build/test_package_templates.py

# 2. Chạy thử nghiệm đóng gói templates giả lập (dry-run)
python3 misc/scripts/package_templates.py --dry-run --output bin/Bamboo_v0.1.0-alpha.1_templates.tpz

# 3. Chạy smoke test trên binary vừa build
python3 misc/scripts/smoke_test.py --binary bin/bamboo.macos.editor.arm64
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Workflow CI desktop (Linux, macOS, Windows) build thành công và cache SCons hoạt động.
2. File `tests/python_build/test_package_templates.py` pass 100%.
3. Script `misc/scripts/smoke_test.py` xác nhận binary khởi động headless thành công và in đúng header Bamboo.
4. Sinh thành công artifact gói template `Bamboo_v0.1.0-alpha.1_templates.tpz` sẵn sàng đính kèm release.
