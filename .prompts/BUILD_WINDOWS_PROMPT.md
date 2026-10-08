# TASK: Build Bamboo Engine Executable for Windows (Editor & Templates)

## VAI TRÒ CỦA BẠN
Bạn là một kỹ sư hệ thống C++ và chuyên gia Build Pipeline có kinh nghiệm sâu sắc về kiến trúc SCons của Godot Engine. Nhiệm vụ của bạn là kiểm tra môi trường, chuẩn bị tài nguyên và biên dịch Bamboo Engine thành file thực thi chạy trên hệ điều hành Windows (`.exe`).

---

## NGUYÊN TẮC AN TOÀN & BẢN QUYỀN
1. **Tuân thủ MIT**: Không xóa/sửa đổi header bản quyền gốc trong source code.
2. **Tránh sửa `thirdparty/`**: Không can thiệp vào các thư viện bên thứ 3 trừ khi cấu hình build yêu cầu cờ liên kết (linking flags).
3. **Thao tác có kiểm soát**: Báo cáo lỗi chi tiết nếu quá trình compile bị ngắt giữa chừng, không tự ý xóa thư mục `bin/` nếu chưa có sự đồng ý.

---

## CÁC BƯỚC THỰC THI (THỰC HIỆN TUẦN TỰ)

### BƯỚC 1: NHẬN DIỆN MÔI TRƯỜNG BUILD & TOOLCHAIN
Kiểm tra xem hệ điều hành hiện tại là gì và xác định chiến lược biên dịch:

1. **Nếu đang chạy trên WINDOWS (Native Build)**:
   - Kiểm tra xem Visual Studio C++ (MSVC) đã được cài đặt chưa: `cl.exe` hoặc môi trường `vcvarsall.bat`.
   - Kiểm tra `scons --version` và `python --version`.
   - Toolchain ưu tiên: **MSVC** (nhanh và tương thích tốt nhất trên Windows).

2. **Nếu đang chạy trên LINUX / macOS (Cross-compilation)**:
   - Kiểm tra xem MinGW-w64 đã được cài đặt chưa:
     - Linux: `x86_64-w64-mingw32-gcc --version`
     - macOS: `x86_64-w64-mingw32-gcc` (cài qua `brew install mingw-w64`).
   - Nếu chưa có MinGW, hãy hướng dẫn lệnh cài đặt phù hợp với OS trước khi tiếp tục.

---

### BƯỚC 2: KIỂM TRA TÀI NGUYÊN WINDOWS (.RC & ICONS)
Trước khi build, đảm bảo thông tin metadata của file `.exe` hiển thị đúng tên Bamboo:

1. Kiểm tra file `platform/windows/godot_res.rc` (hoặc `bamboo_res.rc` nếu đã đổi tên):
   - Kiểm tra các trường:
     - `FileDescription`: Đổi thành "Bamboo Engine"
     - `ProductName`: Đổi thành "Bamboo Engine"
     - `CompanyName`: Cập nhật tên tác giả / Bamboo Team
     - `LegalCopyright`: Cập nhật bản quyền (VD: "Copyright (c) 2026 Bamboo Team. Based on Godot Engine.")
2. Kiểm tra đường dẫn icon: `platform/windows/godot.ico` (hoặc icon tùy chỉnh của Bamboo). Đảm bảo file icon tồn tại để trình liên kết tài nguyên (`windres` hoặc MSVC `rc.exe`) không báo lỗi.

---

### BƯỚC 3: XÂY DỰNG LỆNH SCONS VÀ TIẾN HÀNH BIÊN DỊCH

Hãy xác định số luồng CPU khả dụng (`nproc` trên Linux/macOS hoặc `%NUMBER_OF_PROCESSORS%` trên Windows) để tối ưu tham số `-j`.

Chạy lệnh build phiên bản **Bamboo Editor** cho Windows (x86_64):

```bash
# Đối với bản phát triển/thử nghiệm (Debug/Dev Editor):
scons platform=windows target=editor arch=x86_64 dev_build=yes -j10

# HOẶC đối với bản chính thức (Production Release Editor):
# scons platform=windows target=editor arch=x86_64 production=yes -j<SO_LUONG_CPU>