# TASK [RT/RND]: Xây Dựng Dự Án Đo Lường Hiệu Năng Tự Động (Benchmark Suite v1)

> **Agent**: `RT` (Runtime & Physics) / `RND` (Rendering)  
> **Milestone**: `0.1.0-alpha.2` (Tuần 3–4 · 26/10 – 06/11/2026)  
> **Mục tiêu**: Xây dựng dự án benchmark độc lập, chạy tự động ở chế độ `--headless`, xuất kết quả JSON chuẩn hóa cho ≥ 6 kịch bản hiệu năng, và viết test kiểm chứng runner.

---

## 1. Bối cảnh & Tech Stack
Để phục vụ mục tiêu **O2: Đo lường & Giám sát hiệu năng**, Bamboo Engine cần một bộ benchmark tự động chạy hàng đêm (Nightly CI) để phát hiện sớm các hiện tượng tụt giảm hiệu năng (performance regression):
- Chạy thông qua command line không cần màn hình hiển thị: `--headless`.
- Tự động thoát sau một số khung hình xác định: `--quit-after <N>` hoặc script `get_tree().quit()`.
- Xuất số liệu thống kê ra file JSON chuẩn để so sánh giữa các commit.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Thiết Kế Dự Án Benchmark (`benchmarks/`)
Tạo dự án Godot/Bamboo nhỏ tại `benchmarks/project.godot` chứa 6 kịch bản kiểm thử:
1. **`bench_2d_sprites`**: Render 10.000 sprite di chuyển trên màn hình (đo FPS, frame time, CanvasItem batching).
2. **`bench_3d_draw_calls`**: Lưới 2.500 đối tượng MeshInstance3D với dynamic lighting (đo CPU draw call time).
3. **`bench_physics_3d_stack`**: Tháp 500 khối RigidBody3D va chạm và sụp đổ (đo CPU physics step time với Jolt Physics).
4. **`bench_gdscript_cpu`**: Các thuật toán tính toán CPU-bound (Fibonacci, Vector3 transform, Array sorting).
5. **`bench_startup_time`**: Đo thời gian từ khi gọi process đến khi khung hình đầu tiên sẵn sàng (ms).
6. **`bench_memory_footprint`**: Đo `OS.get_static_memory_usage()` khi tải cảnh phức tạp.

### Bước 2: Viết Harness Runner Script (`benchmarks/scripts/benchmark_runner.gd`)
Script GDScript tự động duyệt qua các scene test, ghi nhận mẫu thông số qua `Performance` singleton (`Performance.TIME_FPS`, `Performance.TIME_PROCESS`, `Performance.MEMORY_STATIC`), tính giá trị trung bình (Average) và phân vị P95, rồi lưu vào `benchmarks/output/results.json`.

### Bước 3: Viết CI Nightly Script (`misc/scripts/run_benchmarks.py`)
Script Python điều khiển chạy engine binary với tham số:
```bash
bin/bamboo.* --headless --path benchmarks/ --script benchmarks/scripts/benchmark_runner.gd
```
Thu thập JSON kết quả, so sánh với `benchmarks/baseline.json`. Nếu hiệu năng sụt giảm quá 5% mà không có giải thích, script cảnh báo exit code non-zero.

### Bước 4: Viết Unit Test Kiểm Tra Benchmark Runner (`tests/python_build/test_benchmark_runner.py`)
Tạo unit test Python kiểm tra:
- Schema của file JSON kết quả xuất ra có đầy đủ 6 kịch bản bắt buộc.
- Các trường số liệu (`fps_avg`, `frame_time_ms`, `physics_time_ms`, `memory_bytes`) có kiểu số dương hợp lệ.
- Logic phát hiện regression so sánh đúng tỷ lệ % sai lệch.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm chứng runner và schema JSON
python3 -m unittest tests/python_build/test_benchmark_runner.py

# 2. Chạy thử nghiệm benchmark suite với binary Bamboo
python3 misc/scripts/run_benchmarks.py --binary bin/bamboo.macos.editor.arm64 --output-json bin/benchmark_v1.json

# 3. Kiểm tra nội dung file kết quả JSON
python3 -c "import json; d=json.load(open('bin/benchmark_v1.json')); print('Scenarios:', len(d.get('benchmarks', [])))"
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Thư mục `benchmarks/` chứa đầy đủ 6 kịch bản hoạt động độc lập và ổn định.
2. Binary Bamboo chạy `--headless` thành công và tự động xuất ra file `results.json` hợp lệ.
3. File test `tests/python_build/test_benchmark_runner.py` pass 100%.
4. Tạo baseline đầu tiên tại `benchmarks/baseline.json` cho bản build `0.1.0-alpha.2`.
