# TASK [RT]: Thiết Lập Jolt 3D Physics Làm Mặc Định & Viết C++ Unit Tests (doctest)

> **Agent**: `RT` (Runtime & Physics)  
> **Milestone**: `0.1.0-alpha.3` (Tuần 5–6 · 09/11 – 20/11/2026)  
> **Mục tiêu**: Chuyển đổi Jolt 3D Physics thành backend vật lý mặc định cho mọi project mới tạo trong Bamboo Engine; xử lý tính tương thích ngược và viết C++ Unit Test (doctest) kiểm thử toàn diện.

---

## 1. Bối cảnh & Tech Stack
- Godot 4.x nguyên bản mặc định sử dụng `GodotPhysics3D`. Tuy nhiên, engine vật lý nội bộ này bị giới hạn về đa luồng, dễ xảy ra hiện tượng xuyên vật thể (jittering) và hiệu năng mô phỏng kém khi có nhiều hơn vài trăm vật thể động.
- `modules/jolt_physics` đã được tích hợp sẵn vào Bamboo Engine và mang lại hiệu năng đa luồng vượt trội (gấp 3–5 lần trong các kịch bản va chạm phức tạp).
- Mục tiêu **O4**: Bật Jolt làm backend mặc định cho mọi dự án Bamboo mới mà không cần người dùng phải vào Project Settings chuyển đổi thủ công.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Điều Chỉnh Giá Trị Mặc Định Trong Core C++
1. Kiểm tra `servers/physics_server_3d_wrap_mt.cpp` và `core/config/project_settings.cpp`:
   - Tìm kiếm setting: `physics/3d/physics_engine`.
   - Đặt giá trị mặc định thành `"JoltPhysics3D"` (kèm comment `// BAMBOO:`):
     ```cpp
     // BAMBOO: Default to JoltPhysics3D for better multi-threaded physics performance.
     GLOBAL_DEF("physics/3d/physics_engine", "JoltPhysics3D");
     ```
2. Kiểm tra fallback an toàn:
   - Nếu bản build tắt module Jolt (`module_jolt_physics_enabled=no`), engine phải tự động fallback về `"GodotPhysics3D"` kèm in log cảnh báo thân thiện thay vì crash.

### Bước 2: Viết C++ Unit Test Cho Jolt Physics (`tests/servers/test_jolt_physics_default.cpp`)
Tạo file test mới sử dụng framework doctest của Bamboo Engine:

```cpp
#include "tests/test_macros.h"

TEST_FORCE_LINK(test_jolt_physics_default)

#include "core/config/project_settings.h"
#include "servers/physics_server_3d.h"
#include "scene/3d/physics/rigid_body_3d.h"
#include "scene/3d/physics/collision_shape_3d.h"
#include "scene/resources/3d/box_shape_3d.h"

namespace TestJoltPhysicsDefault {

TEST_CASE("[JoltPhysics] Verify default physics engine setting") {
    String engine_name = GLOBAL_GET("physics/3d/physics_engine");
    CHECK_EQ(engine_name, String("JoltPhysics3D"));
}

TEST_CASE("[JoltPhysics] Simulate RigidBody3D fall under gravity") {
    // Khởi tạo một RigidBody3D và một BoxShape3D
    RigidBody3D *body = memnew(RigidBody3D);
    CollisionShape3D *cshape = memnew(CollisionShape3D);
    Ref<BoxShape3D> box;
    box.instantiate();
    box->set_size(Vector3(1, 1, 1));
    cshape->set_shape(box);
    body->add_child(cshape);

    body->set_position(Vector3(0, 10, 0));
    
    // Kiểm tra trạng thái khởi tạo
    CHECK_EQ(body->get_position().y, doctest::Approx(10.0));

    // Dọn dẹp bộ nhớ
    memdelete(cshape);
    memdelete(body);
}

} // namespace TestJoltPhysicsDefault
```

### Bước 3: Đăng Ký Test Vào Hệ Thống Build (`tests/SCsub`)
- Cập nhật file `tests/SCsub` để biên dịch `test_jolt_physics_default.cpp` khi chạy SCons với cờ `tests=yes`.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Biên dịch engine với tests=yes
scons platform=macos target=editor tests=yes dev_build=yes -j$(nproc)

# 2. Chạy test suite chỉ định cho Jolt Physics
bin/bamboo.macos.editor.arm64 --test --test-case="*[JoltPhysics]*"

# 3. Chạy headless project kiểm tra setting in ra màn hình
bin/bamboo.macos.editor.arm64 --headless --eval "print('Physics Engine:', ProjectSettings.get_setting('physics/3d/physics_engine'))" --quit
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. `bin/bamboo.* --test --test-case="*[JoltPhysics]*"` chạy pass 100%.
2. Khi tạo project mới trong Bamboo Editor, `Project Settings > Physics > 3D > Physics Engine` mặc định hiển thị `JoltPhysics3D`.
3. Kiểm thử với project cũ cấu hình `GodotPhysics3D`: engine vẫn nhận diện đúng và không ghi đè cài đặt người dùng cũ.
4. Mọi đoạn code sửa đổi đều có tag `// BAMBOO:` đầy đủ.
