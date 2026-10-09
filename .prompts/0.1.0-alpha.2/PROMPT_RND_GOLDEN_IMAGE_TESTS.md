# TASK [RND]: Xây Dựng Hệ Thống Kiểm Thử Đồ Họa Golden-Image Cho 3 Renderer

> **Agent**: `RND` (Rendering Engine)  
> **Milestone**: `0.1.0-alpha.2` (Tuần 3–4 · 26/10 – 06/11/2026)  
> **Mục tiêu**: Xây dựng hệ thống Golden-Image regression test tự động cho cả 3 renderer (Forward+, Mobile, Compatibility); kiểm thử độ sai lệch hình ảnh có ngưỡng sai số (image diff threshold) và viết unit test cho thuật toán so sánh ảnh.

---

## 1. Bối cảnh & Tech Stack
Bamboo Engine hỗ trợ 3 backend đồ họa chính:
1. **Forward+** (Clustered Vulkan / D3D12 / Metal): Đồ họa cao cấp cho PC/Desktop.
2. **Mobile** (Vulkan Mobile / Metal): Đồ họa tối ưu cho điện thoại di động tầm trung.
3. **Compatibility** (OpenGL ES 3.0 / WebGL 2): Tương thích máy cấu hình thấp và Web.

Mỗi khi có commit thay đổi shader hoặc rendering server, nguy cơ xảy ra lỗi hiển thị (visual regression) rất cao. Do CI runner thường không có GPU vật lý rời, giải pháp là sử dụng **software rasterizer** (`llvmpipe` / `lavapipe` trên Linux) kết hợp Metal trên runner macOS, chụp ảnh khung hình mẫu và so sánh với ảnh chuẩn (Golden Images).

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Xây Dựng Cảnh Kiểm Thử Chuẩn (`tests/visual/scenes/`)
Tạo các scene chuẩn đại diện cho các tính năng render trọng yếu:
- `test_pbr_materials.tscn`: Khối cầu PBR kiểm tra Roughness, Metallic, Normal mapping, Albedo.
- `test_shadow_mapping.tscn`: Nguồn sáng Directional & Omni light chiếu bóng đổ lên bề mặt.
- `test_alpha_blending.tscn`: Các lớp kính và hạt trong suốt kiểm tra thứ tự sắp xếp độ sâu (depth sorting).
- `test_canvas_item_2d.tscn`: Đối chiếu rendering 2D pixel-perfect giữa Forward+ và Compatibility.

### Bước 2: Viết Harness Chụp Ảnh Render Mẫu (`misc/scripts/capture_golden_images.py`)
Script Python chạy Bamboo Engine xuất ảnh render ở frame thứ 10 (sau khi shader compile xong):
```bash
bin/bamboo.* --rendering-method <forward_plus|mobile|gl_compatibility> \
             --headless --write-movie tests/visual/output/<scene>_<method>.png \
             tests/visual/scenes/<scene>.tscn
```

### Bước 3: Hiện Thực Thuật Toán So Sánh Ảnh (`misc/scripts/compare_images.py`)
Sử dụng thư viện Python `Pillow` để so sánh ảnh kết quả với ảnh mẫu gốc (`tests/visual/golden/`):
- Tính toán sai số trung bình (Mean Absolute Error / Root Mean Square Error trên từng kênh RGBA).
- Cho phép ngưỡng dung sai chấp nhận được (Tolerance threshold: $\le 1.5\%$ pixel diff) do sai số giữa các driver phần mềm GPU.
- Tự động xuất ảnh phân biệt sai khác (`diff.png`) với các điểm lỗi được bôi đỏ nổi bật khi vượt ngưỡng.

### Bước 4: Viết Unit Test Kiểm Tra Bộ So Sánh Ảnh (`tests/python_build/test_golden_image_diff.py`)
Tạo unit test Python kiểm tra thuật toán:
- Hai ảnh giống hệt nhau phải trả về sai số `0.0%` (Pass).
- Hai ảnh sai khác hoàn toàn (đen vs trắng) phải trả về sai số `100.0%` (Fail).
- Kiểm tra cơ chế tolerance threshold: ảnh có vài pixel lệch nhỏ dưới ngưỡng cho phép vẫn trả về `Pass`.
- Kiểm tra tính năng tạo file `diff.png` khi xảy ra lỗi.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy unit test kiểm tra thuật toán so sánh ảnh
python3 -m unittest tests/python_build/test_golden_image_diff.py

# 2. Chạy thử nghiệm chụp và so sánh 1 cảnh chuẩn
python3 misc/scripts/compare_images.py \
    --expected tests/visual/golden/test_pbr_forward_plus.png \
    --actual tests/visual/output/test_pbr_forward_plus.png \
    --threshold 0.02
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Có ít nhất 4 scene đồ họa chuẩn được xây dựng tại `tests/visual/scenes/`.
2. Hệ thống chạy ổn định trên CI Linux không có GPU thật qua `llvmpipe`.
3. File test `tests/python_build/test_golden_image_diff.py` pass 100%.
4. Đóng gói bộ ảnh Golden Image baseline vào thư mục `tests/visual/golden/`.
