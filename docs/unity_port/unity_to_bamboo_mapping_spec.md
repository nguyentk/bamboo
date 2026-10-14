# Unity3D → Bamboo Engine: Đặc tả Ánh xạ Kỹ thuật

> Sprint `0.1.0-alpha.1` · Agent GAME/PLT · Tài liệu nền cho pipeline port game Unity nội bộ sang Bamboo.
> Schema máy đọc được: [`tools/unity_importer/schema/unity_to_bamboo_spec.json`](../../tools/unity_importer/schema/unity_to_bamboo_spec.json)
> Code chuyển hệ tọa độ: [`tools/unity_importer/coordinate_conversion.py`](../../tools/unity_importer/coordinate_conversion.py)
> Kiểm thử: [`tests/python_build/test_unity_mapping_spec.py`](../../tests/python_build/test_unity_mapping_spec.py)

---

## 1. Khảo sát dự án Unity

### 1.1 Công cụ

```bash
python3 tools/unity_importer/survey_unity_project.py /path/to/UnityProject
```

```bash
python3 tools/unity_importer/survey_unity_project.py /path/to/UnityProject --json --output docs/unity_port/survey_<game>.json
```

Yêu cầu: dự án Unity dùng **Asset Serialization = Force Text** (Project Settings → Editor). Công cụ cảnh báo nếu gặp asset binary.

Công cụ thống kê:
- Scene `.unity`, prefab, prefab variant, script C#.
- Component theo nhóm: physics, rendering, animation, audio, VFX, UI, navigation (đọc class ID trong YAML Unity).
- Đặc điểm script: `MonoBehaviour`, `ScriptableObject`, `UnityEvent`, C# event/`Action`, coroutine, Input cũ / New Input System, TextMeshPro, Addressables, DOTween, async/await.
- Asset: model, texture, audio, material, shader/Shader Graph, VFX Graph, Animator Controller, Animation Clip, PhysicMaterial, `.inputactions`, UI Toolkit.
- Render pipeline (Built-in / URP / HDRP) và package từ `Packages/manifest.json`.

### 1.2 Kết quả khảo sát game được chọn

> **Trạng thái: chờ dữ liệu.** Chưa có dự án Unity nội bộ trong repo. Khi đội GAME chọn game, chạy công cụ ở §1.1 và điền bảng dưới đây (lưu JSON vào `docs/unity_port/survey_<game>.json`).

| Hạng mục | Số lượng | Ghi chú / rủi ro |
| :--- | :---: | :--- |
| Scene `.unity` | – | |
| Prefab / Prefab Variant | – / – | |
| Script C# (MonoBehaviour / ScriptableObject) | – / – | |
| Render pipeline | – | URP → Forward+/Mobile; HDRP → rủi ro cao |
| Physics (Rigidbody, Collider, CharacterController) | – | |
| Animator Controller / Animation Clip | – / – | |
| Particle System / VFX Graph | – / – | VFX Graph không có tương đương trực tiếp |
| UI (Canvas, TextMeshPro, UI Toolkit) | – | |
| Input (cũ / New Input System) | – | |
| Package bên thứ 3 (DOTween, Addressables, SDK…) | – | |

### 1.3 Tiêu chí chọn game (đề xuất cho TL + GAME)
- Thể loại 2D hoặc 3D mid-core, gameplay hoàn chỉnh, ≤ 20 scene, ≤ 300 script.
- URP hoặc Built-in (tránh HDRP).
- Ít phụ thuộc package đóng (Asset Store binary DLL, SDK native).
- Có thể đo hiệu năng so sánh trên PC + Android.

---

## 2. Hệ tọa độ

| | Unity | Bamboo (Godot) |
| :--- | :--- | :--- |
| Tay | Trái (left-handed) | Phải (right-handed) |
| Trục lên | +Y | +Y |
| Hướng trước (forward) | +Z | **−Z** |
| Trục phải | +X | +X |
| Đơn vị | mét | mét |

**Quy tắc chuyển đổi — lật trục Z** (soi gương qua mặt phẳng XY, `M = diag(1, 1, −1)`):

| Đại lượng | Unity | Bamboo |
| :--- | :--- | :--- |
| Vị trí | `(x, y, z)` | `(x, y, −z)` |
| Hướng (direction) | `(x, y, z)` | `(x, y, −z)` |
| Tỉ lệ (scale) | `(x, y, z)` | `(x, y, z)` |
| Quaternion | `(x, y, z, w)` | `(−x, −y, z, w)` |

Giải thích quaternion: `R' = M·R·M`; trục quay là pseudovector nên biến thành `det(M)·M·axis = (−ax, −ay, az)`, góc giữ nguyên. Test tự động kiểm chứng trên 200 phép quay ngẫu nhiên rằng *quay rồi chuyển* bằng *chuyển rồi quay*.

**Phạm vi áp dụng**: transform được serialize trong scene/prefab Unity (`m_LocalPosition`, `m_LocalRotation`, `m_LocalScale`) và vector hướng trong dữ liệu game. **Không** áp dụng cho dữ liệu mesh nhập từ FBX/glTF — importer của Bamboo (ufbx, glTF) đã tự chuyển trục.

---

## 3. Ánh xạ khái niệm cốt lõi

| Khái niệm Unity | Tương đương Bamboo | Hướng dẫn chuyển đổi |
| :--- | :--- | :--- |
| `GameObject` | `Node3D` / `Node2D` / `Control` / `Node` | Chọn theo component: 3D → `Node3D`, 2D → `Node2D`, UI → `Control` |
| `Transform` | `Node3D.transform` (`Basis` + `Vector3`) | Gộp vào chính node; áp dụng §2 |
| `RectTransform` | `Control` (anchors, offsets, pivot) | Anchor min/max → `anchor_*`, sizeDelta/anchoredPosition → `offset_*` |
| `Prefab` | `PackedScene` (`.tscn`) | `instantiate()` + `add_child()` |
| `Prefab Variant` | Scene kế thừa (Inherited Scene) | Kế thừa từ `.tscn` gốc |
| Scene `.unity` | `PackedScene` (`.tscn`) | `get_tree().change_scene_to_file()` |
| `ScriptableObject` | `Resource` tùy biến (`.tres`) | Class `extends Resource` với `@export` |
| `MonoBehaviour` | Script gắn vào node (GDScript `extends Node3D`, hoặc C#) | Một node có **một** script; nhiều MonoBehaviour → node con hoặc gộp |
| `UnityEvent` / C# event | `signal` + `connect()` | Kết nối trong editor hoặc code |
| Layer / Tag | `collision_layer`/`collision_mask` (bitmask) / Group | Tag → `add_to_group()` |
| `DontDestroyOnLoad` | Autoload (singleton) | Project Settings → Autoload |

## 4. Vòng đời script

| Unity | Bamboo | Ghi chú |
| :--- | :--- | :--- |
| `Awake()` | `_init()` / `_enter_tree()` | `_init` chạy trước khi vào cây; cần truy cập cây thì dùng `_enter_tree` |
| `OnEnable()` | `_enter_tree()` | Hoặc theo dõi `visible` / `process_mode` |
| `Start()` | `_ready()` | Gọi một lần, con trước cha |
| `Update()` | `_process(delta)` | |
| `FixedUpdate()` | `_physics_process(delta)` | |
| `LateUpdate()` | `_process(delta)` với `process_priority` cao hơn | |
| `OnDisable()` | `_exit_tree()` | |
| `OnDestroy()` | `_notification(NOTIFICATION_PREDELETE)` | |
| `OnCollisionEnter` | signal `body_entered` của `RigidBody3D` | Bật `contact_monitor`, đặt `max_contacts_reported > 0` |
| `OnTriggerEnter/Exit` | signal `body_entered/exited` của `Area3D` | |

## 5. API thường dùng

| Unity | Bamboo |
| :--- | :--- |
| `Instantiate(prefab)` | `prefab.instantiate()` + `add_child()` |
| `Destroy(obj)` | `queue_free()` |
| `GetComponent<T>()` | `get_node()` / `$Child` / tham chiếu `@export` |
| `SendMessage` | `call()` / `propagate_call()` |
| `StartCoroutine` | `await` (signal, `get_tree().create_timer()`) |
| `Invoke(name, t)` | `get_tree().create_timer(t).timeout.connect(...)` |
| `PlayerPrefs` | `ConfigFile` lưu ở `user://` |
| `Time.deltaTime` | tham số `delta` |
| `Debug.Log` | `print()` |
| `Input.GetAxis` / `GetButtonDown` | `Input.get_axis()` / `Input.is_action_just_pressed()` |
| `Physics.Raycast` | `RayCast3D` hoặc `PhysicsDirectSpaceState3D.intersect_ray()` |

## 6. Component

| Unity | Bamboo | Ghi chú |
| :--- | :--- | :--- |
| `MeshFilter` + `MeshRenderer` | `MeshInstance3D` | |
| `SkinnedMeshRenderer` | `MeshInstance3D` + `Skeleton3D` | |
| `Camera` | `Camera3D` | |
| `Light` (Directional/Point/Spot) | `DirectionalLight3D` / `OmniLight3D` / `SpotLight3D` | Đơn vị cường độ khác → hiệu chỉnh lại |
| `Rigidbody` | `RigidBody3D` (Jolt) | |
| `Rigidbody` kinematic | `AnimatableBody3D` / `CharacterBody3D` | |
| `CharacterController` | `CharacterBody3D` | `Move()` → `velocity` + `move_and_slide()` |
| `Box/Sphere/CapsuleCollider` | `CollisionShape3D` + `BoxShape3D`/`SphereShape3D`/`CapsuleShape3D` | Node con của body |
| `MeshCollider` | `CollisionShape3D` + `ConcavePolygonShape3D` (hoặc `ConvexPolygonShape3D` nếu convex) | |
| Collider `isTrigger` | `Area3D` | |
| `PhysicMaterial` | `PhysicsMaterial` | dynamicFriction → friction, bounciness → bounce |
| `Rigidbody2D`, `BoxCollider2D`, `CircleCollider2D`, `PolygonCollider2D` | `RigidBody2D`, `CollisionShape2D`+`RectangleShape2D`/`CircleShape2D`, `CollisionPolygon2D` | |
| `SpriteRenderer` / `Tilemap` | `Sprite2D` / `TileMapLayer` | |
| `Animator` | `AnimationTree` + `AnimationPlayer` | State machine → `AnimationNodeStateMachine` |
| `Animation` (legacy) | `AnimationPlayer` | |
| `AudioSource` / `AudioListener` | `AudioStreamPlayer3D` (hoặc `AudioStreamPlayer` nếu 2D) / `AudioListener3D` | |
| `ParticleSystem` | `GPUParticles3D` / `CPUParticles3D` | |
| `NavMeshAgent` / NavMeshSurface | `NavigationAgent3D` / `NavigationRegion3D` | |
| `Canvas` | `CanvasLayer` + `Control` gốc | |
| `Image` / `Text` / `TextMeshProUGUI` / `Button` | `TextureRect` / `Label` / `RichTextLabel` / `Button` | |
| Volume (post-processing URP/HDRP) | `WorldEnvironment` + `Environment` | |
| `Terrain` | — | Không có sẵn: dùng mesh heightmap hoặc addon |

## 7. Kiểu dữ liệu

| Unity (C#) | Bamboo |
| :--- | :--- |
| `int`, `float`, `double`, `bool`, `string` | `int`, `float`, `float`, `bool`, `String` |
| `Vector2/3/4`, `Vector2Int/3Int` | `Vector2/3/4`, `Vector2i/3i` |
| `Quaternion`, `Color`, `Color32` | `Quaternion`, `Color`, `Color` |
| `Rect`, `Bounds`, `Matrix4x4` | `Rect2`, `AABB`, `Projection` |
| `List<T>`, `T[]`, `Dictionary<K,V>` | `Array[T]`, `Array[T]`, `Dictionary[K, V]` |
| `GameObject`, `Transform` | `Node`, `Node3D` |
| `Sprite`, `AudioClip`, `AnimationClip`, `Material`, `Mesh` | `Texture2D`, `AudioStream`, `Animation`, `Material`, `Mesh` |
| `LayerMask` | `int` (bitmask) |
| `Action`, `Func<T>` | `Callable` |

## 8. Material, Input

| Unity | Bamboo | Quy tắc |
| :--- | :--- | :--- |
| URP/Lit | `StandardMaterial3D` | `roughness = 1 − smoothness`; metallic giữ nguyên; normal map kiểm tra quy ước DirectX/OpenGL |
| URP/Unlit | `StandardMaterial3D` (`shading_mode = unshaded`) | |
| Shader Graph | `VisualShader` hoặc `.gdshader` | Port thủ công |
| Input Manager / New Input System | `InputMap` actions | Định nghĩa trong Project Settings → Input Map |

## 9. Rủi ro đã biết

| Hạng mục | Rủi ro | Hướng xử lý |
| :--- | :--- | :--- |
| Nhiều `MonoBehaviour` trên một `GameObject` | Bamboo chỉ một script mỗi node | Tách thành node con theo chức năng hoặc gộp script |
| VFX Graph, HDRP | Không có tương đương trực tiếp | Viết lại bằng `GPUParticles3D` / shader; tránh chọn game HDRP |
| Asset Store DLL đóng, SDK native | Không port được trực tiếp | Thay bằng plugin Bamboo / GDExtension |
| Terrain | Không có node terrain sẵn | Addon hoặc mesh heightmap |
| C# → GDScript | Viết lại logic | Có thể giữ C# nếu build Bamboo kèm module .NET (`module_mono_enabled=yes`, tắt mặc định); C# không xuất được lên Web |

## 10. Bước tiếp theo (Sprint 0.1.0-alpha.2)
- Chạy khảo sát trên game được chọn, điền §1.2, chốt scope.
- Xây asset converter (model/texture/prefab → `.tscn`) dựa trên schema JSON — prompt `PROMPT_GAME_UNITY_ASSET_CONVERTER.md`.
