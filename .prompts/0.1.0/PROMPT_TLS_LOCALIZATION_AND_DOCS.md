# TASK [TLS]: Cập Nhật File Ngôn Ngữ (.pot) & Hoàn Thiện Tài Liệu Migration Guide "Unity to Bamboo"

> **Agent**: `TLS` (Tools & Editor)  
> **Milestone**: `0.1.0` (Tuần 9 · 07/12 – 11/12/2026)  
> **Mục tiêu**: Cập nhật file mẫu dịch thuật `.pot` cho toàn bộ các chuỗi giao diện đã đổi tên Bamboo; hoàn thiện bộ tài liệu hướng dẫn kỹ thuật "Unity3D sang Bamboo Engine Migration Guide" và viết unit test kiểm tra cú pháp file dịch.

---

## 1. Bối cảnh & Tech Stack
- Giao diện Bamboo Editor hỗ trợ đa ngôn ngữ thông qua hệ thống dịch Gettext (`.po` / `.pot`).
- Do các chuỗi hiển thị thương hiệu đã được cập nhật từ Godot sang Bamboo (tiêu đề cửa sổ, thông báo khởi động, giới thiệu About, nút phiên bản), cần sinh lại file mẫu dịch thuật `editor/translations/editor.pot`.
- Đồng thời, để hỗ trợ các đội ngũ game nội bộ và đối tác di chuyển dự án, tài liệu hướng dẫn chuyển đổi từ Unity3D sang Bamboo cần được hoàn thiện chi tiết, chuẩn xác kèm code mẫu.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Sinh Lại File Mẫu Bản Dịch (`editor.pot`)
Chạy script trích xuất chuỗi gettext từ mã nguồn C++ của Editor:
```bash
python3 misc/scripts/make_pot.py
```
Kiểm tra các chuỗi `Bamboo Engine`, `Sprout`, `bamboo_string` xuất hiện đúng ngữ cảnh trong file `editor/translations/editor.pot`.

### Bước 2: Hoàn Thiện Tài Liệu Hướng Dẫn Migration (`docs/unity_port/Unity_to_Bamboo_Migration_Guide.md`)
Biên soạn tài liệu hướng dẫn chi tiết gồm các chương:
1. **Tổng quan mô hình tư duy**: GameObject + Component vs Node Hierarchy + Scene Composition.
2. **Bảng tra cứu API Cheat-sheet**:
   - `Transform.position` $\rightarrow$ `global_position`
   - `GameObject.Find()` $\rightarrow$ `get_node()` / `find_child()`
   - `Instantiate()` $\rightarrow$ `packed_scene.instantiate()`
   - `Destroy()` $\rightarrow$ `queue_free()`
   - `StartCoroutine()` $\rightarrow$ `await get_tree().create_timer(1.0).timeout`
3. **Chuyển đổi Shader & Vật liệu**: Standard/URP Lit sang `StandardMaterial3D`.
4. **Vật lý Jolt 3D**: Rigidbody, Colliders, Physics Layers và Masks.
5. **Đóng gói & Tối ưu kích thước**: Sử dụng 3 build profile `bamboo_2d`, `bamboo_mobile`, `bamboo_pc`.

### Bước 3: Viết Unit Test Kiểm Tra File Dịch Thuật (`tests/python_build/test_localization_pot.py`)
Tạo unit test Python:
- Kiểm tra tính hợp lệ cú pháp của file `editor/translations/editor.pot`.
- Kiểm tra không có `msgid` bị trùng lặp.
- Đảm bảo các chuỗi ký tự định dạng (format specifiers: `%s`, `%d`) khớp nhau giữa msgid và các bản dịch.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm chứng file dịch .pot
python3 -m unittest tests/python_build/test_localization_pot.py

# 2. Kiểm tra tài liệu Migration Guide
head -n 50 docs/unity_port/Unity_to_Bamboo_Migration_Guide.md
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. File `editor/translations/editor.pot` được cập nhật đồng bộ với mã nguồn C++ mới nhất.
2. File test `tests/python_build/test_localization_pot.py` pass 100%.
3. Tài liệu [docs/unity_port/Unity_to_Bamboo_Migration_Guide.md](file:///Users/khuyennguyen/Projects/Bamboo/bamboo/docs/unity_port/Unity_to_Bamboo_Migration_Guide.md) được hoàn thiện với đầy đủ bảng tra cứu và code mẫu trực quan.
