# TASK [TLS]: Chuẩn Hóa C++ Dual-Versioning, UI Editor & C++ Unit Tests (doctest)

> **Agent**: `TLS` (Tools & Editor)  
> **Milestone**: `0.1.0-alpha.1` (Tuần 1–2 · 12/10 – 23/10/2026)  
> **Mục tiêu**: Đảm bảo toàn bộ kiến trúc C++ Dual-Versioning hoạt động chuẩn xác, tích hợp chuỗi Bamboo vào Editor UI, và viết C++ Unit Test (doctest) kiểm thử toàn diện.

---

## 1. Bối cảnh & Tech Stack
- File `version.py` định nghĩa song song hai bộ số:
  - Godot base (`major = 4`, `minor = 8`, `patch = 0`) nhằm bảo vệ tính tương thích của GDExtension ABI và project tag.
  - Bamboo version (`bamboo_major = 0`, `bamboo_minor = 1`, `bamboo_patch = 0`, `bamboo_prerelease = "alpha.1"`, `bamboo_codename = "Sprout"`).
- `core/core_builders.py` sinh ra `core/version_generated.gen.h` chứa các macro C++:
  - `BAMBOO_VERSION_MAJOR`, `BAMBOO_VERSION_MINOR`, `BAMBOO_VERSION_PATCH`, `BAMBOO_VERSION_PRERELEASE`, `BAMBOO_VERSION_CODENAME`, `BAMBOO_VERSION_STRING`.
- `core/config/engine.cpp` bổ sung các trường vào dictionary trả về từ `Engine.get_version_info()`.
- Framework test: C++ **doctest** trong `tests/` (`#include "tests/test_macros.h"`).

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Rà soát & Đảm bảo Tính Nhất Quán Của Macro C++
1. Kiểm tra `core/version.h` và `core/version_generated.gen.h`:
   - Đảm bảo macro `BAMBOO_VERSION_FULL_BUILD` được định nghĩa chính xác.
   - Đảm bảo chuỗi `GODOT_VERSION_FULL_NAME` được định dạng là:
     `"Bamboo Engine v" BAMBOO_VERSION_STRING " (Godot " GODOT_VERSION_FULL_CONFIG ")"`
2. Kiểm tra `main/main.cpp`:
   - Hàm `print_header()` phải in đúng tên và phiên bản Bamboo khi khởi động.
3. Kiểm tra `editor/gui/editor_version_button.cpp`:
   - Nút hiển thị phiên bản ở thanh trạng thái dưới cùng của Editor hiển thị chuỗi `v0.1.0-alpha.1 (Sprout)`.
   - Nút copy clipboard sao chép chuỗi phiên bản đầy đủ.

### Bước 2: Viết C++ Unit Test (`tests/core/config/test_bamboo_version.cpp`)
Tạo file test mới sử dụng framework doctest của Bamboo/Godot:

```cpp
#include "tests/test_macros.h"

TEST_FORCE_LINK(test_bamboo_version)

#include "core/config/engine.h"
#include "core/version.h"

namespace TestBambooVersion {

TEST_CASE("[BambooVersion] Check Bamboo version fields in Engine singleton") {
    Dictionary version_info = Engine::get_singleton()->get_version_info();

    // 1. Kiểm tra các trường Bamboo tồn tại
    CHECK(version_info.has("bamboo_major"));
    CHECK(version_info.has("bamboo_minor"));
    CHECK(version_info.has("bamboo_patch"));
    CHECK(version_info.has("bamboo_prerelease"));
    CHECK(version_info.has("bamboo_codename"));
    CHECK(version_info.has("bamboo_string"));

    // 2. Kiểm tra giá trị phiên bản alpha.1
    CHECK_EQ(int(version_info["bamboo_major"]), 0);
    CHECK_EQ(int(version_info["bamboo_minor"]), 1);
    CHECK_EQ(int(version_info["bamboo_patch"]), 0);
    CHECK_EQ(String(version_info["bamboo_prerelease"]), String("alpha.1"));
    CHECK_EQ(String(version_info["bamboo_codename"]), String("Sprout"));
    CHECK_EQ(String(version_info["bamboo_string"]), String("0.1.0-alpha.1"));

    // 3. Đảm bảo số phiên bản Godot gốc không bị phá vỡ (bảo vệ ABI GDExtension)
    CHECK_EQ(int(version_info["major"]), 4);
    CHECK_EQ(int(version_info["minor"]), 8);
}

TEST_CASE("[BambooVersion] Verify C++ Preprocessor Macros") {
    CHECK_EQ(BAMBOO_VERSION_MAJOR, 0);
    CHECK_EQ(BAMBOO_VERSION_MINOR, 1);
    CHECK_EQ(BAMBOO_VERSION_PATCH, 0);
    CHECK_EQ(String(BAMBOO_VERSION_STRING), String("0.1.0-alpha.1"));
}

} // namespace TestBambooVersion
```

### Bước 3: Đăng Ký Test Vào Hệ Thống Build (`tests/SCsub`)
- Cập nhật file `tests/SCsub` để biên dịch `tests/core/config/test_bamboo_version.cpp` khi bật cờ `tests=yes`.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Biên dịch engine kèm bộ test suite
scons platform=macos target=editor tests=yes dev_build=yes -j$(nproc)

# 2. Chạy test suite chỉ định cho Bamboo Version
bin/bamboo.macos.editor.arm64 --test --test-case="*[BambooVersion]*"

# 3. Chạy toàn bộ test core để đảm bảo không có regression
bin/bamboo.macos.editor.arm64 --test --test-case="*[ProjectSettings]*"
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Lệnh `bin/bamboo.* --test --test-case="*[BambooVersion]*"` chạy thành công (0 failures).
2. Khi mở Editor GUI, nút trạng thái phía dưới hiển thị đúng nhãn `v0.1.0-alpha.1 (Sprout)`.
3. Lệnh `bin/bamboo.* --version` in đúng định dạng phiên bản máy đọc được cho CI.
4. Mọi patch trong C++ đều có comment `// BAMBOO:` đầy đủ.
