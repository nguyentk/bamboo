# TASK [GAME]: Triển Khai Game Lên PC & Android, Thu Thập Crash Dump & Telemetry

> **Agent**: `GAME` (Dogfooding & Unity Porting) / `PLT`  
> **Milestone**: `0.1.0-beta.1` (Tuần 7 · 23/11 – 27/11/2026)  
> **Mục tiêu**: Export và cài đặt thành công game dogfood lên PC (Windows/macOS) và thiết bị Android thật; tích hợp cơ chế thu thập crash dump kèm thông tin phiên bản Bamboo; viết unit test kiểm tra hệ thống telemetry.

---

## 1. Bối cảnh & Tech Stack
Dogfooding thực tế là bước kiểm tra gắt gao nhất cho một engine mới:
- Game cần được export bằng chính template release của Bamboo Engine đã build ở các sprint trước.
- Khi chạy trên Android (thiết bị tầm trung chạy Snapdragon / MediaTek), cần kiểm tra:
  - Khả năng tương thích driver đồ họa Vulkan / GLES3.
  - Xử lý safe area màn hình tai thỏ / nốt ruồi.
  - Cơ chế bắt lỗi và xuất log crash rõ ràng khi game gặp sự cố.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Cấu Hình Export Preset Cho PC & Android
1. Tạo preset export trong `game_dogfood/export_presets.cfg`:
   - Android: Đặt Package Unique Name (vd: `com.bamboo.dogfoodgame`), Min SDK 24, Target SDK 34, Keystore debug.
   - Desktop: Window size 1920x1080, VSync Enabled.
2. Thực hiện lệnh export CLI:
   ```bash
   # Export Android APK
   bin/bamboo.macos.editor.arm64 --headless --path game_dogfood/ --export-debug "Android" bin/game_dogfood.apk
   ```

### Bước 2: Tích Hợp Crash Reporting Script (`game_dogfood/scripts/crash_reporter.gd`)
Tạo module bắt lỗi và log hệ thống:
```gdscript
extends Node

func _ready() -> void:
    var v_info := Engine.get_version_info()
    var bamboo_ver: String = v_info.get("bamboo_string", "unknown")
    print("[Telemetry] Initializing game session on Bamboo Engine: ", bamboo_ver)
    print("[Telemetry] Device Model: ", OS.get_model_name(), " | OS: ", OS.get_name())

func log_error(context: String, err_msg: String) -> void:
    var report = {
        "timestamp": Time.get_datetime_string_from_system(),
        "bamboo_version": Engine.get_version_info().get("bamboo_string", ""),
        "context": context,
        "error": err_msg
    }
    var file := FileAccess.open("user://crash_log.json", FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(report))
        file.close()
```

### Bước 3: Cài Đặt Lên Thiết Bị & Kiểm Thử Thực Tế
1. Cài đặt APK qua ADB:
   ```bash
   adb install -r bin/game_dogfood.apk
   adb logcat -s BambooEngine:V Godot:V
   ```
2. Cho tester chơi liên tục 15 phút, theo dõi nhiệt độ máy, hiện tượng giật khung hình (frame drops) và độ ổn định vật lý Jolt.

### Bước 4: Viết Unit Test Kiểm Tra Crash Reporter (`tests/game/test_crash_reporter.gd`)
Tạo test GDScript:
- Gọi hàm `log_error()` với dữ liệu giả lập.
- Đọc lại file `user://crash_log.json`.
- Kiểm tra nội dung JSON phải chứa đúng khóa `bamboo_version` (vd: `0.1.0-beta.1`) và chuỗi lỗi.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test headless kiểm tra Crash Reporter
bin/bamboo.macos.editor.arm64 --headless --path game_dogfood/ -s tests/game/test_crash_reporter.gd

# 2. Kiểm tra logcat Android khi khởi chạy game
adb logcat -d | grep -i "bamboo"
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. File `game_dogfood.apk` cài đặt và chạy mượt mà trên thiết bị Android thật không bị crash khi khởi động.
2. Bản build PC chạy đạt $\ge 60$ FPS ổn định.
3. Test script `tests/game/test_crash_reporter.gd` pass 100%.
4. Không có lỗi rò rỉ bộ nhớ nghiêm trọng (memory leak) sau 15 phút chơi liên tục.
