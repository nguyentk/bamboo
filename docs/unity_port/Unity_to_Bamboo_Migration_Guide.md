# Hướng dẫn chuyển đổi Unity3D sang Bamboo Engine

> Bamboo Engine 0.1 "Sprout" (dựa trên Godot 4.8). Dành cho lập trình viên và kỹ thuật viên đã quen Unity.
> Tài liệu tham chiếu chi tiết: [unity_to_bamboo_mapping_spec.md](unity_to_bamboo_mapping_spec.md) · Schema máy đọc: [`tools/unity_importer/schema/unity_to_bamboo_spec.json`](../../tools/unity_importer/schema/unity_to_bamboo_spec.json)
> Dự án mẫu: [`game_dogfood/`](../../game_dogfood/) (nhân vật, vật lý Jolt, vật phẩm, HUD, telemetry, export).

---

## 1. Mô hình tư duy

| Unity | Bamboo | Điều cần nhớ |
| :--- | :--- | :--- |
| `GameObject` + nhiều `Component` | **Node** có kiểu riêng, ghép thành **cây** | Thay vì "thêm component Rigidbody", bạn dùng node `RigidBody3D` và gắn các node con (`CollisionShape3D`, `MeshInstance3D`) |
| Scene `.unity` / Prefab `.prefab` | **Scene** `.tscn` — cả level lẫn prefab đều là scene | Prefab = scene được *instance* vào scene khác |
| Prefab Variant | **Scene kế thừa** (New Inherited Scene) | Ghi đè thuộc tính của scene gốc |
| Nhiều `MonoBehaviour` trên một object | **Một script mỗi node** | Tách chức năng thành node con, hoặc gộp script |
| `ScriptableObject` | **Resource** tùy biến (`.tres`) | `class_name GameConfig extends Resource` + `@export` |
| `UnityEvent` / C# `event` | **Signal** | Kết nối trong editor (dock Node → Signals) hoặc `connect()` |
| Tag | **Group** | `add_to_group("enemies")`, `get_tree().get_nodes_in_group("enemies")` |
| `DontDestroyOnLoad` / singleton | **Autoload** | Project Settings → Globals → Autoload |

Hệ tọa độ: cả hai đều Y-up, đơn vị mét. Unity "trước mặt" là **+Z**, Bamboo là **−Z** (hệ tay phải). Công cụ chuyển đổi tự lật trục Z cho transform trong scene/prefab; mesh nhập từ FBX/glTF đã được importer tự chuyển, **không** lật lại.

## 2. Vòng đời script

```csharp
// Unity (C#)
public class Player : MonoBehaviour {
    public float speed = 8f;
    Rigidbody rb;
    void Awake()  { rb = GetComponent<Rigidbody>(); }
    void Start()  { Debug.Log("Ready"); }
    void Update() { /* input, UI */ }
    void FixedUpdate() { /* physics */ }
    void OnDestroy() { }
}
```

```gdscript
# Bamboo (GDScript)
extends CharacterBody3D

@export var speed := 8.0          # [SerializeField] / public field -> @export

func _ready() -> void:            # Start (Awake: _init / _enter_tree)
    print("Ready")

func _process(delta: float) -> void:          # Update
    pass

func _physics_process(delta: float) -> void:  # FixedUpdate
    pass

func _exit_tree() -> void:        # OnDisable / OnDestroy
    pass
```

| Unity | Bamboo |
| :--- | :--- |
| `Awake` | `_init()` (chưa vào cây) hoặc `_enter_tree()` |
| `OnEnable` / `OnDisable` | `_enter_tree()` / `_exit_tree()` |
| `Start` | `_ready()` — con chạy trước cha |
| `Update` / `FixedUpdate` | `_process(delta)` / `_physics_process(delta)` |
| `LateUpdate` | `_process()` với `process_priority` lớn hơn |
| `OnDestroy` | `_notification(NOTIFICATION_PREDELETE)` |
| `OnCollisionEnter` | signal `body_entered` của `RigidBody3D` (bật `contact_monitor`, `max_contacts_reported > 0`) |
| `OnTriggerEnter` / `Exit` | signal `body_entered` / `body_exited` của `Area3D` |

## 3. API cheat-sheet

| Unity | Bamboo |
| :--- | :--- |
| `transform.position` | `global_position` (`position` là tọa độ cục bộ) |
| `transform.localPosition` | `position` |
| `transform.rotation` (Quaternion) | `global_transform.basis.get_rotation_quaternion()` / `quaternion` |
| `transform.forward` | `-global_transform.basis.z` |
| `GameObject.Find("Player")` | `get_node("/root/Main/Player")`, `$Player`, `find_child("Player")` |
| `GetComponent<T>()` | `get_node("Child") as T`, `$Child`, hoặc `@export var target: T` |
| `Instantiate(prefab)` | `var n = packed_scene.instantiate(); add_child(n)` |
| `Destroy(obj)` | `obj.queue_free()` |
| `StartCoroutine(Wait())` | `await get_tree().create_timer(1.0).timeout` |
| `yield return null` | `await get_tree().process_frame` |
| `Invoke("Fire", 2f)` | `get_tree().create_timer(2.0).timeout.connect(fire)` |
| `SceneManager.LoadScene("Level2")` | `get_tree().change_scene_to_file("res://scenes/level2.tscn")` |
| `PlayerPrefs.SetInt("score", 10)` | `ConfigFile` lưu ở `user://` |
| `Time.deltaTime` | tham số `delta` |
| `Debug.Log(x)` | `print(x)` |
| `Mathf.Lerp(a, b, t)` | `lerp(a, b, t)` |
| `Input.GetAxis("Horizontal")` | `Input.get_axis("move_left", "move_right")` |
| `Input.GetButtonDown("Jump")` | `Input.is_action_just_pressed("jump")` |
| `Physics.Raycast(...)` | node `RayCast3D`, hoặc `get_world_3d().direct_space_state.intersect_ray(...)` |

Coroutine sang `await`:

```csharp
IEnumerator FlashThenHide() {
    renderer.enabled = false;
    yield return new WaitForSeconds(0.2f);
    renderer.enabled = true;
}
```

```gdscript
func flash_then_hide() -> void:
    visible = false
    await get_tree().create_timer(0.2).timeout
    visible = true
```

UnityEvent sang signal:

```gdscript
signal coin_collected(total: int)

func collect_coin() -> void:
    coins += 1
    coin_collected.emit(coins)

# Ở nơi khác:
player.coin_collected.connect(hud.on_coin_collected)
```

## 4. Input

1. Project Settings → **Input Map** → tạo action (`move_forward`, `move_back`, `move_left`, `move_right`, `jump`, `fire`) và gán phím/gamepad. Ví dụ đầy đủ trong `game_dogfood/project.godot`.
2. Đọc input:

```gdscript
var dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
if Input.is_action_just_pressed("jump") and is_on_floor():
    velocity.y = jump_velocity
```

## 5. Vật lý (Jolt)

Project Bamboo mới **mặc định dùng Jolt Physics** (`physics/3d/physics_engine = "Jolt Physics"`). Project cũ giữ engine đã cấu hình; nếu engine yêu cầu không có trong bản build, Bamboo in cảnh báo và dùng engine mặc định.

| Unity | Bamboo |
| :--- | :--- |
| `Rigidbody` | `RigidBody3D` |
| `Rigidbody.isKinematic` | `AnimatableBody3D` (di chuyển bằng animation/code) hoặc `CharacterBody3D` |
| `CharacterController.Move(v * dt)` | `velocity = v` rồi `move_and_slide()` |
| `BoxCollider` / `SphereCollider` / `CapsuleCollider` | `CollisionShape3D` + `BoxShape3D` / `SphereShape3D` / `CapsuleShape3D` (node con của body) |
| `MeshCollider` (convex / không convex) | `ConvexPolygonShape3D` / `ConcavePolygonShape3D` |
| `isTrigger` | `Area3D` |
| `PhysicMaterial` | `PhysicsMaterial` (`friction`, `bounce`) |
| Layer + Layer Collision Matrix | `collision_layer` (object thuộc lớp nào) + `collision_mask` (object va chạm với lớp nào), mỗi bit một lớp |

Đặt tên layer: Project Settings → Layer Names → 3D Physics. Điều khiển nhân vật mẫu: [`game_dogfood/scripts/player_controller.gd`](../../game_dogfood/scripts/player_controller.gd).

## 6. Material & Shader

| Unity | Bamboo | Quy tắc |
| :--- | :--- | :--- |
| Standard / URP Lit | `StandardMaterial3D` | `albedo_color` = `_Color`/`_BaseColor`; `roughness = 1 − smoothness` (`_Glossiness`/`_Smoothness`); `metallic` giữ nguyên; `normal_texture` từ `_BumpMap` (cùng quy ước OpenGL +Y, không cần lật) |
| URP Unlit | `StandardMaterial3D` với `shading_mode = UNSHADED` | |
| Tiling / Offset | `uv1_scale` / `uv1_offset` | |
| Shader Graph | Visual Shader hoặc `.gdshader` | Port thủ công |
| Volume (post-processing) | `WorldEnvironment` + `Environment` (glow, tonemap, SSAO, fog…) | |

Chuyển material tự động:

```bash
python3 tools/unity_importer/mat_converter.py --input Assets/Materials/Enemy.mat --output game/assets/enemy.tres --unity-project /path/to/UnityProject
```

## 7. Pipeline chuyển đổi tự động

1. **Khảo sát dự án** (Asset Serialization = Force Text):

```bash
python3 tools/unity_importer/survey_unity_project.py /path/to/UnityProject --json --output survey.json
```

2. **Model & texture**: copy file `.fbx`/`.gltf`/`.png` vào project Bamboo — editor tự import (giữ cấu trúc thư mục `Assets/` dưới `res://assets/` để đường dẫn material khớp).
3. **Material**: `mat_converter.py` (mục 6).
4. **Prefab → scene**:

```bash
python3 tools/unity_importer/prefab_to_tscn.py --input Assets/Prefabs/Enemy.prefab --output game/scenes/enemy.tscn
```

   Kết quả giữ cây node, transform (đã lật trục Z), collider; GUID mesh được lưu ở `metadata/unity_mesh_guid` để gán mesh sau khi import model.
5. **Script**: viết lại theo mục 2–4 (chưa có chuyển C# tự động).

## 8. Đóng gói & tối ưu kích thước

Export templates Bamboo được cài từ file `.tpz` (Editor → Manage Export Templates → Install From File). Bamboo có 3 build profile (`profiles/`):

| Profile | Dùng cho | Template release macOS arm64 (đo thực tế) |
| :--- | :--- | :--- |
| Mặc định / `bamboo_pc` | Game PC đầy đủ tính năng | 58.9 MB |
| `bamboo_2d` | Game 2D (bỏ 3D, vật lý/navigation 3D, XR; `-Os`) | 41.3 MB (−30%) |
| `bamboo_mobile` | Android/iOS (`-Os`, bỏ XR/WebRTC/raycast) | 47.8 MB (−19%) |

Build template theo profile:

```bash
scons platform=android target=template_release profile=profiles/bamboo_mobile.py
```

Số liệu đầy đủ: [`docs/reports/binary_size_benchmark.md`](../reports/binary_size_benchmark.md).

## 9. Những gì chưa có tương đương trực tiếp

| Unity | Hướng xử lý trong Bamboo 0.1 |
| :--- | :--- |
| VFX Graph | `GPUParticles3D` + particle shader |
| HDRP | Renderer Forward+ (chất lượng thấp hơn HDRP) |
| Terrain | Addon terrain hoặc mesh heightmap |
| Timeline / Cinemachine | `AnimationPlayer` (Timeline/Virtual Camera nằm trong roadmap 2027) |
| Addressables | Gói `.pck` tải thêm (roadmap Bamboo Services) |
| Asset Store DLL đóng | Thay bằng addon / GDExtension |
| C# trên Web | Không hỗ trợ — dùng GDScript cho game Web |
