# TASK [BQ]: Thiết Lập 3 Build Profiles (2D, Mobile, PC) & Đo Đạc Kích Thước Binary

> **Agent**: `BQ` (Build & CI) / `PLT`  
> **Milestone**: `0.1.0-alpha.3` (Tuần 5–6 · 09/11 – 20/11/2026)  
> **Mục tiêu**: Xây dựng 3 cấu hình build profile chuyên biệt (`bamboo_2d`, `bamboo_mobile`, `bamboo_pc`) để tối ưu triệt để dung lượng binary xuất xưởng; viết công cụ đo đạc tự động và unit test kiểm tra profile.

---

## 1. Bối cảnh & Tech Stack
Một trong những lợi thế cạnh tranh lớn nhất của Bamboo Engine so với Unity là **kích thước binary nhỏ gọn** và khả năng strip mạnh mẽ các module không dùng:
- Game 2D không cần hệ thống 3D (CSG, GridMap, Jolt Physics 3D, 3D Renderers Clustered). Tắt 3D (`disable_3d=yes`) giúp giảm 30–50% dung lượng binary.
- Game Mobile cần lược bỏ các module desktop cồng kềnh (OpenXR, WebXR, Raycasting phức tạp) để tối ưu dung lượng tải về từ Google Play / App Store.
- Hệ thống SCons của Godot hỗ trợ nạp file cấu hình thông qua tham số `profile=...` hoặc `build_profile=...`.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Xây Dựng 3 File Cấu Hình Build Profile (`profiles/`)
Tạo thư mục `profiles/` và các file cấu hình tương ứng:
1. **`profiles/bamboo_2d.py`**:
   ```python
   # Bamboo Engine - 2D Dedicated Build Profile
   disable_3d = "yes"
   module_csg_enabled = "no"
   module_gridmap_enabled = "no"
   module_jolt_physics_enabled = "no"
   module_godot_physics_3d_enabled = "no"
   module_openxr_enabled = "no"
   module_glslang_enabled = "yes"
   ```
2. **`profiles/bamboo_mobile.py`**:
   ```python
   # Bamboo Engine - Mobile Optimized Build Profile
   module_openxr_enabled = "no"
   module_raycast_enabled = "no"
   module_webrtc_enabled = "no"
   optimize = "size"  # -Os flag
   ```
3. **`profiles/bamboo_pc.py`**: Cấu hình đầy đủ tính năng (Full features).

### Bước 2: Tạo File Export Profile Editor (`.gdbuild`)
Tạo các preset `.gdbuild` tương ứng để lập trình viên có thể chọn trực tiếp trong giao diện Export của Editor khi build game ra thành phẩm.

### Bước 3: Viết Script Đo Đạc & So Sánh Binary (`misc/scripts/measure_binary_sizes.py`)
Script Python tự động:
- Đọc kích thước file nhị phân trong thư mục `bin/`.
- Tạo bảng so sánh Markdown giữa bản Full và các bản build profile (kích thước uncompressed và sau khi nén `.zip` / `.gz`).
- Lưu kết quả vào `docs/reports/binary_size_benchmark.md`.

### Bước 4: Viết Unit Test Kiểm Tra Build Profiles (`tests/python_build/test_build_profiles.py`)
Tạo unit test Python kiểm tra:
- Các file profile Python trong `profiles/` có cú pháp hợp lệ và không chứa cờ SCons bị deprecated.
- Profile `bamboo_2d.py` bắt buộc phải có `disable_3d = "yes"`.
- Script đo kích thước xử lý chính xác khi file tồn tại và báo lỗi hợp lý khi file chưa được build.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm chứng cú pháp và quy chuẩn của các profiles
python3 -m unittest tests/python_build/test_build_profiles.py

# 2. Thử nghiệm lệnh build SCons với profile 2D (dry-run)
scons platform=macos target=template_release profile=profiles/bamboo_2d.py -n

# 3. Chạy script đo đạc kích thước binary hiện có
python3 misc/scripts/measure_binary_sizes.py --bin-dir bin/ --output docs/reports/binary_size_benchmark.md
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Thư mục `profiles/` chứa đầy đủ 3 profile hoạt động ổn định.
2. Bản build `bamboo_2d` giảm được ít nhất 25% kích thước file thực thi so với bản build tiêu chuẩn.
3. File test `tests/python_build/test_build_profiles.py` pass 100%.
4. Báo cáo đối chuẩn kích thước binary được xuất bản tại `docs/reports/binary_size_benchmark.md`.
