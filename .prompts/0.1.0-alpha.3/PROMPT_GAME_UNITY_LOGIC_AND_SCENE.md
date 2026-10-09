# TASK [GAME]: Chuyển Đổi Script Logic MonoBehaviour Sang Bamboo & Ghép Cảnh Hoàn Chỉnh

> **Agent**: `GAME` (Dogfooding & Unity Porting) / `RT`  
> **Milestone**: `0.1.0-alpha.3` (Tuần 5–6 · 09/11 – 20/11/2026)  
> **Mục tiêu**: Chuyển đổi mã nguồn gameplay C# MonoBehaviour của game Unity nội bộ sang GDScript/C# của Bamboo Engine; cấu hình Input Actions, va chạm Jolt Physics, ghép hoàn chỉnh scene game chính và viết unit test kiểm tra logic điều khiển.

---

## 1. Bối cảnh & Tech Stack
Sau khi đã chuyển đổi thành công Models, Textures và Materials ở alpha.2, bước then chốt tiếp theo là đưa **Logic vận hành (Gameplay Code)** và **Cấu trúc Scene** vào Bamboo Engine:
- **MonoBehaviour sang Node Script**:
  - `Awake()` / `Start()` $\rightarrow$ `_ready()`
  - `Update()` $\rightarrow$ `_process(delta)`
  - `FixedUpdate()` $\rightarrow$ `_physics_process(delta)`
- **Điều khiển nhân vật & Vật lý**:
  - Unity `CharacterController.Move()` hoặc `Rigidbody.velocity` $\rightarrow$ Bamboo `CharacterBody3D` với `velocity` và `move_and_slide()`.
  - Unity `OnTriggerEnter(Collider)` $\rightarrow$ Bamboo Signal `body_entered` của `Area3D`.
- **Hệ thống đầu vào (Input)**:
  - Unity `Input.GetAxisRaw("Horizontal")` $\rightarrow$ Bamboo `Input.get_axis("move_left", "move_right")`.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Thiết Lập Dự Án Game Dogfood (`game_dogfood/`)
Tạo thư mục dự án game nội bộ tại `game_dogfood/project.godot`:
- Cấu hình Input Map (`move_forward`, `move_back`, `move_left`, `move_right`, `jump`, `fire`).
- Kích hoạt Jolt 3D Physics backend.
- Cấu hình độ phân giải và window mode chuẩn mobile/PC.

### Bước 2: Chuyển Đổi Controller Nhân Vật (`game_dogfood/scripts/player_controller.gd`)
Viết lại logic điều khiển nhân vật từ bản Unity:
```gdscript
extends CharacterBody3D

@export var speed: float = 8.0
@export var jump_velocity: float = 4.5
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y -= gravity * delta

    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = jump_velocity

    var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    if direction:
        velocity.x = direction.x * speed
        velocity.z = direction.z * speed
    else:
        velocity.x = move_toward(velocity.x, 0, speed)
        velocity.z = move_toward(velocity.z, 0, speed)

    move_and_slide()
```

### Bước 3: Ghép Cảnh Hoàn Chỉnh (`game_dogfood/scenes/main_level.tscn`)
- Ráp mô hình môi trường (terrain/level geometry đã convert từ Unity).
- Gắn `CollisionShape3D` tương ứng cho sàn và vật cản tĩnh.
- Instance scene `player.tscn` và các đối tượng tương tác/kẻ địch.

### Bước 4: Viết Test Kiểm Tra Gameplay Logic (`tests/game/test_gameplay_logic.gd` / Python Harness)
Tạo bài test tự động chạy qua lệnh CLI:
- Khởi tạo instance của `player_controller.gd`.
- Giả lập nhận tín hiệu input di chuyển -> Kiểm tra vector `velocity` thay đổi chính xác.
- Giả lập rơi tự do -> Kiểm tra gia tốc trọng trường tác động lên `velocity.y`.
- Kiểm tra tín hiệu tương tác `body_entered` được kích hoạt khi va chạm với vật phẩm mẫu.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test gameplay logic ở chế độ headless
bin/bamboo.macos.editor.arm64 --headless --path game_dogfood/ -s tests/game/test_gameplay_logic.gd

# 2. Khởi chạy thử game mẫu trực tiếp trên Editor
bin/bamboo.macos.editor.arm64 --path game_dogfood/

# 3. Export thử nghiệm game dogfood sang binary macOS
bin/bamboo.macos.editor.arm64 --headless --path game_dogfood/ --export-debug "macOS" bin/game_dogfood.app
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Dự án `game_dogfood/` mở được trong Bamboo Editor mà không có bất kỳ script error nào.
2. Nhân vật di chuyển mượt mà, va chạm ổn định trên sàn và tường với Jolt Physics.
3. Test script `tests/game/test_gameplay_logic.gd` pass 100%.
4. Game có thể xuất xưởng binary chạy thử nghiệm độc lập trên Desktop.
