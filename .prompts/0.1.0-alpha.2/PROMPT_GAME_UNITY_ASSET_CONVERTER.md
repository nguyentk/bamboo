# TASK [GAME]: Xây Dựng Công Cụ Chuyển Đổi Asset (Materials, Textures, Prefabs) Từ Unity3D

> **Agent**: `GAME` (Dogfooding & Unity Porting) / `TLS`  
> **Milestone**: `0.1.0-alpha.2` (Tuần 3–4 · 26/10 – 06/11/2026)  
> **Mục tiêu**: Xây dựng bộ công cụ tự động chuyển đổi tài nguyên game từ Unity3D sang Bamboo Engine (Materials, Textures, Prefabs sang `.tscn`), kèm bộ Unit Test kiểm chứng dữ liệu chuyển đổi.

---

## 1. Bối cảnh & Tech Stack
Khi chuyển một dự án từ Unity3D sang Bamboo Engine, việc chuyển đổi thủ công hàng trăm tài nguyên đồ họa (Textures, Materials, Prefabs) là không khả thi và dễ sai sót:
- Unity Material (`.mat` file ở dạng YAML text) sử dụng các thuộc tính shader như `_Color`, `_MainTex`, `_Metallic`, `_Glossiness`, `_BumpMap`.
- Bamboo Material (`.tres` file định dạng Text Resource) sử dụng `StandardMaterial3D` với `albedo_color`, `albedo_texture`, `metallic`, `roughness` (lưu ý: `roughness = 1.0 - _Glossiness`), `normal_texture`.
- Unity Prefab (`.prefab` dạng YAML) chứa cây phân cấp `GameObject` và `Transform` cần được ánh xạ sang định dạng file cảnh `.tscn` của Bamboo.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Xây Dựng Parser Material Unity (`tools/unity_importer/mat_converter.py`)
Script Python đọc file `.mat` của Unity và xuất file `.tres` của Bamboo:
- Trích xuất mã màu RGBA từ `_Color` và chuyển thành `Color(r, g, b, a)`.
- Ánh xạ đường dẫn texture `_MainTex` sang `res://assets/...`.
- Tính toán độ nhám: `roughness = 1.0 - float(glossiness)`.
- Tạo file resource text chuẩn của Bamboo:
  ```ini
  [gd_resource type="StandardMaterial3D" format=3]

  [resource]
  albedo_color = Color(1, 1, 1, 1)
  roughness = 0.5
  metallic = 0.0
  ```

### Bước 2: Xây Dựng Parser Prefab Sang Scene (`tools/unity_importer/prefab_to_tscn.py`)
Script Python đọc cấu trúc GameObject trong file `.prefab`:
- Đọc Transform (Position, Rotation quaternion, Scale).
- Chuyển đổi hệ tọa độ từ Left-handed (Unity) sang Right-handed (Bamboo: đảo dấu trục Z).
- Tạo cấu trúc scene `.tscn`:
  ```ini
  [gd_scene format=3]

  [node name="Root" type="Node3D"]

  [node name="MeshInstance" type="MeshInstance3D" parent="."]
  transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
  ```

### Bước 3: Viết Unit Test Kiểm Tra Chuyển Đổi Asset (`tests/python_build/test_unity_asset_converter.py`)
Tạo unit test Python kiểm tra:
1. **Material Test**:
   - Truyền file `.mat` mẫu có `_Glossiness: 0.8` -> File `.tres` xuất ra phải có `roughness = 0.2` (sai số $\le 0.001$).
   - Kiểm tra định dạng màu RGBA được làm tròn hợp lệ.
2. **Transform / Coordinate Test**:
   - Kiểm tra phép xoay và vị trí vector: vị trí `Vector3(1, 2, 3)` từ Unity phải được ánh xạ sang tọa độ Right-handed chính xác `Vector3(1, 2, -3)` trên Bamboo.
3. **Hierarchy Test**:
   - Prefab có 3 cấp node con lồng nhau phải sinh đúng thuộc tính `parent="."` hoặc `parent="NodeName"` trong file `.tscn`.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy bộ unit test kiểm chứng chuyển đổi tài nguyên Unity
python3 -m unittest tests/python_build/test_unity_asset_converter.py

# 2. Thử nghiệm chuyển đổi 1 material mẫu
python3 tools/unity_importer/mat_converter.py \
    --input tests/data/sample_unity_mat.mat \
    --output bin/sample_material.tres

# 3. Mở file .tres sinh ra và kiểm tra định dạng
cat bin/sample_material.tres
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Script `mat_converter.py` và `prefab_to_tscn.py` hoạt động ổn định trên các file YAML mẫu.
2. File test `tests/python_build/test_unity_asset_converter.py` pass 100%.
3. Toàn bộ models và materials của game Unity nội bộ được chuyển đổi thử nghiệm sang thư mục dự án `game_dogfood/` và mở được trong Bamboo Editor mà không bị lỗi texture bị thiếu.
