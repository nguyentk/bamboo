# TASK [PLT]: Thiết Lập CI Mobile (Android/iOS) & Web, Cấu Hình Ký Số

> **Agent**: `PLT` (Platform & Mobile) / `BQ`  
> **Milestone**: `0.1.0-alpha.2` (Tuần 3 · 26/10 – 30/10/2026)  
> **Mục tiêu**: Mở rộng CI matrix trên GitHub Actions cho Android (APK/AAB), iOS và Web (HTML5/Wasm); cấu hình lưu trữ chứng chỉ ký số; viết test kiểm tra tính toàn vẹn của CI workflows.

---

## 1. Bối cảnh & Tech Stack
Sau khi hoàn thành CI Desktop ở alpha.1, Bamboo Engine cần mở rộng biên dịch tự động sang 3 nền tảng mục tiêu then chốt:
1. **Android**: SCons kết hợp Android NDK (r25+), Gradle build xuất `android_source.zip` và các template thư viện `.so` (`arm64-v8a`, `armeabi-v7a`, `x86_64`).
2. **iOS**: Xcode toolchain xuất `.a` / `libbamboo.ios.template_*.a` và đóng gói xcframework/zip.
3. **Web**: Emscripten SDK (`emcc`) biên dịch WebAssembly (Wasm) với cả 2 biến thể: đa luồng (`threads=yes`) và đơn luồng (`threads=no`).

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Cấu hình Workflow Android (`.github/workflows/android_builds.yml`)
- Cấu hình cài đặt JDK 17, Android SDK & NDK r25c.
- Lệnh biên dịch SCons:
  ```bash
  scons platform=android target=template_release arch=arm64 build_name=bamboo engine_update_check=no dev_build=no
  scons platform=android target=template_release arch=arm32 build_name=bamboo engine_update_check=no dev_build=no
  ```
- Chạy Gradle đóng gói templates APK/AAB và lưu artifact.

### Bước 2: Cấu hình Workflow iOS & Web (`ios_builds.yml`, `web_builds.yml`)
- **iOS**: Chạy trên runner `macos-14`, biên dịch architecture `arm64` cho thiết bị thật và `simulator`.
- **Web**: Cài đặt `emsdk`, kích hoạt cờ Wasm thích hợp (`threads=yes` và `threads=no`).

### Bước 3: Chuẩn Bị Kho Khóa Ký Số (Code Signing Secrets)
- Thiết lập kịch bản ký số tự động trên CI:
  - Windows: Ký mã qua `signtool.exe` với chứng chỉ lưu trong GitHub Secrets.
  - macOS: Ký mã `codesign` với Developer ID Application Certificate và `notarytool` (chuẩn bị cho W9).
  - Android: Keystore ký phát hành APK/AAB.

### Bước 4: Viết Unit Test Kiểm Tra Workflow (`tests/python_build/test_mobile_web_workflows.py`)
Tạo test Python kiểm tra tính đúng đắn của toàn bộ file workflow YAML:
- Phân tích cú pháp YAML không có lỗi thụt dòng.
- Kiểm tra ma trận `arch` đầy đủ (`arm64`, `arm32`, `x86_64` cho Android).
- Đảm bảo tất cả lệnh build đều truyền cờ `build_name=bamboo` và `engine_update_check=no`.
- Kiểm tra tính tồn tại của các bước cache toolchain (NDK, Emscripten cache).

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test kiểm tra cấu hình workflow CI Mobile/Web
python3 -m unittest tests/python_build/test_mobile_web_workflows.py

# 2. Kiểm tra cú pháp YAML cục bộ (yêu cầu pyyaml)
python3 -c "import yaml; [yaml.safe_load(open(f)) for f in ['.github/workflows/android_builds.yml', '.github/workflows/ios_builds.yml', '.github/workflows/web_builds.yml']]"
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Các workflow `android_builds.yml`, `ios_builds.yml`, `web_builds.yml` chạy xanh trên GitHub Actions.
2. File test `tests/python_build/test_mobile_web_workflows.py` pass 100%.
3. Sinh thành công template binary Android `.so` và template Web `.wasm` làm artifact.
4. Tài liệu hướng dẫn cấu hình GitHub Secrets cho ký số được lưu tại `docs/guides/code_signing.md`.
