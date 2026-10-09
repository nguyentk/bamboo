# TASK [RT/GAME]: Lập Báo Cáo Đối Chuẩn Hiệu Năng Unity3D vs Bamboo Engine (Parity Benchmark)

> **Agent**: `RT` (Runtime & Physics) / `GAME`  
> **Milestone**: `0.1.0-beta.1` (Tuần 8 · 30/11 – 04/12/2026)  
> **Mục tiêu**: Tiến hành đo đạc đối chuẩn toàn diện giữa bản game gốc trên Unity3D và bản game đã port trên Bamboo Engine; lập báo cáo so sánh chi tiết và viết unit test kiểm tra công cụ tổng hợp số liệu.

---

## 1. Bối cảnh & Mục Tiêu Đối Chuẩn
Để kiểm chứng giá trị kỹ thuật của việc chuyển đổi sang Bamboo Engine, nhóm phát triển cần số liệu đo đạc khách quan và định lượng giữa hai phiên bản game chạy cùng màn chơi và số lượng entity tương đương:
- **Tiêu chí so sánh**:
  1. **FPS trung bình & 1% Low FPS**: Đo độ mượt mà và hiện tượng giật cục.
  2. **Draw Calls & Batching**: Hiệu quả gộp lệnh vẽ của Renderer.
  3. **Mức tiêu thụ bộ nhớ RAM**: So sánh giữa Garbage Collection của C# Unity và bộ nhớ native gọn nhẹ của Bamboo.
  4. **Kích thước file cài đặt**: Dung lượng APK Android và gói cài đặt Desktop.
  5. **Thời gian khởi động lạnh (Cold Startup Time)**: Tốc độ mở game đến khi vào gameplay.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Quy Trình Thu Thập Dữ Liệu Thực Nghiệm
1. Chạy bản build Unity3D trên thiết bị chuẩn (PC: Intel Core i7 / RTX 3060; Android: Snapdragon 778G).
   - Bật Profiler Unity, ghi nhận số liệu trong 1.000 frame liên tục.
2. Chạy bản build Bamboo Engine tương ứng trên cùng thiết bị và cùng điều kiện môi trường.
   - Bật Engine Profiler, xuất dữ liệu JSON qua script benchmark.

### Bước 2: Viết Script Tổng Hợp & So Sánh Chỉ Số (`misc/scripts/compare_unity_bamboo_metrics.py`)
Script Python nhận đầu vào là 2 file log JSON (Unity log và Bamboo log), tự động tính toán tỷ lệ chênh lệch (%) và sinh bảng đối chuẩn Markdown:
```python
# Ví dụ tính toán % cải thiện
perf_gain = ((bamboo_fps - unity_fps) / unity_fps) * 100
size_reduction = ((unity_size - bamboo_size) / unity_size) * 100
```

### Bước 3: Xuất Bản Báo Cáo Kỹ Thuật (`docs/reports/unity_vs_bamboo_parity_report.md`)
Báo cáo hoàn chỉnh gồm:
- Bảng so sánh 6 chỉ tiêu kỹ thuật cốt lõi.
- Đánh giá về trải nghiệm vật lý (Jolt Physics vs Unity PhysX).
- Các điểm Bamboo vượt trội (dung lượng binary nhẹ hơn ~40%, RAM thấp hơn ~30%).
- Các điểm cần tối ưu tiếp trong Q1/2027 (shader pre-warming trên mobile để triệt tiêu stuttering).

### Bước 4: Viết Unit Test Kiểm Tra Script Tổng Hợp (`tests/python_build/test_parity_reporter.py`)
Tạo unit test Python kiểm tra:
- Khả năng đọc và parse đúng định dạng log JSON từ hai nguồn.
- Công thức tính toán sai lệch phần trăm chính xác tuyệt đối.
- Sinh đúng định dạng bảng Markdown tiêu chuẩn.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm chứng script so sánh
python3 -m unittest tests/python_build/test_parity_reporter.py

# 2. Sinh báo cáo đối chuẩn từ dữ liệu mẫu
python3 misc/scripts/compare_unity_bamboo_metrics.py \
    --unity tests/data/unity_benchmark_sample.json \
    --bamboo tests/data/bamboo_benchmark_sample.json \
    --output docs/reports/unity_vs_bamboo_parity_report.md
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Báo cáo `docs/reports/unity_vs_bamboo_parity_report.md` được hoàn thiện với số liệu đo đạc thực tế.
2. File test `tests/python_build/test_parity_reporter.py` pass 100%.
3. Bản game Bamboo chứng minh được kích thước cài đặt nhỏ hơn $\ge 30\%$ và thời gian khởi động nhanh hơn so với Unity3D.
