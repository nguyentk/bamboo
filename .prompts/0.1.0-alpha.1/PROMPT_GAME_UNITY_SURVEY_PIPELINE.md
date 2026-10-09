# TASK [GAME]: Khảo Sát Kiến Trúc Game Unity3D & Thiết Kế Schema Ánh Xạ Sang Bamboo

> **Agent**: `GAME` (Dogfooding & Unity Porting) / `PLT`  
> **Milestone**: `0.1.0-alpha.1` (Tuần 1–2 · 12/10 – 23/10/2026)  
> **Mục tiêu**: Khảo sát mã nguồn dự án game Unity3D nội bộ được chọn, lập báo cáo phân tích kiến trúc, xây dựng bảng ánh xạ (Mapping Specification) và kiểm thử tính hợp lệ của Schema chuyển đổi.

---

## 1. Bối cảnh & Mục Tiêu Porting
Để phục vụ mục tiêu **O6: Pipeline & Thực Chiến Port Game Unity3D**, đội phát triển cần chọn 1 dự án game nội bộ (ưu tiên thể loại 2D/3D mid-core, hành động hoặc casual có gameplay hoàn chỉnh) để di chuyển sang Bamboo Engine.
Nhiệm vụ đầu tiên là mổ xẻ kiến trúc game Unity hiện tại, phân loại tài nguyên và định nghĩa quy tắc ánh xạ chuẩn xác sang hệ thống Node/Scene của Bamboo.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Khảo Sát Tài Nguyên & Kiến Trúc Dự Án Unity3D
1. Lập danh mục tài nguyên của dự án Unity:
   - **Scenes & Prefabs**: Số lượng `.unity` scene, số lượng `.prefab` và Prefab Variants.
   - **Scripts C#**: Số lượng `MonoBehaviour`, các interface, scriptable objects, event systems (`UnityEvent`, `Action`).
   - **Vật lý**: Cấu trúc `Rigidbody`, `CharacterController`, `BoxCollider`, `MeshCollider`, PhysicMaterials.
   - **Đồ họa & Shaders**: Định dạng model 3D (`.fbx`, `.obj`), textures (`.png`, `.tga`), URP lit materials, particle systems (`ParticleSystem` / VFX Graph).
   - **UI & Input**: Cấu trúc `Canvas`, `RectTransform`, `TextMeshPro`, Input Manager / New Input System.

### Bước 2: Xây Dựng Bản Ánh Xạ Kỹ Thuật (`docs/unity_port/unity_to_bamboo_mapping_spec.md`)
Tài liệu hóa bảng đối chiếu chi tiết:
| Khái niệm Unity3D | Tương đương trên Bamboo Engine | Hướng dẫn chuyển đổi |
| :--- | :--- | :--- |
| `GameObject` | `Node` / `Node3D` / `Node2D` | Cây node phân cấp trực tiếp |
| `Prefab` | `PackedScene` (`.tscn`) | Lưu thành file scene độc lập và instance |
| `Prefab Variant` | Kế thừa Scene (`Scene Inheritance`) | Mở rộng từ base `.tscn` |
| `Transform` | `Node3D.transform` (Basis + Vector3) | Hệ trục tọa độ: chuyển từ Left-handed (Unity) sang Right-handed (Bamboo: Y up, -Z forward) |
| `MonoBehaviour` | `GDScript` (`extends Node3D`) hoặc C# script | Chuyển `Awake()`/`Start()` sang `_ready()`, `Update()` sang `_process()` |
| `Rigidbody` | `RigidBody3D` (Jolt Physics) | Sử dụng backend Jolt Physics mặc định của Bamboo |
| `BoxCollider` | `CollisionShape3D` + `BoxShape3D` | Node con của Body |
| `UnityEvent` | `signal` + `connect()` | Thay thế bằng cơ chế Signal chuẩn của Bamboo |

### Bước 3: Định Nghĩa Schema Chuyển Đổi (`tools/unity_importer/schema/unity_to_bamboo_spec.json`)
Tạo file schema JSON mô tả quy tắc chuyển đổi các thuộc tính Transform, Node hierarchy, và Components sang định dạng scene của Bamboo.

### Bước 4: Viết Unit Test Kiểm Thử Schema (`tests/python_build/test_unity_mapping_spec.py`)
Tạo unit test Python để kiểm chứng:
- Schema JSON có cú pháp hợp lệ và đầy đủ các trường bắt buộc (`node_type_mapping`, `transform_conversion`, `lifecycle_methods`).
- Kiểm tra ma trận chuyển đổi tọa độ (Left-handed sang Right-handed) tính toán chính xác trên các vector mẫu (X, Y, Z).
- Kiểm tra tính đầy đủ của từ điển ánh xạ kiểu dữ liệu (vd: `Vector3` -> `Vector3`, `Quaternion` -> `Quaternion`, `Color` -> `Color`).

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy unit test kiểm tra schema ánh xạ Unity -> Bamboo
python3 -m unittest tests/python_build/test_unity_mapping_spec.py

# 2. Kiểm tra tính hợp lệ cú pháp của file schema JSON
python3 -c "import json; json.load(open('tools/unity_importer/schema/unity_to_bamboo_spec.json'))"
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. Hoàn thành tài liệu phân tích kỹ thuật tại `docs/unity_port/unity_to_bamboo_mapping_spec.md`.
2. File schema `tools/unity_importer/schema/unity_to_bamboo_spec.json` được định nghĩa chuẩn xác.
3. Unit test `tests/python_build/test_unity_mapping_spec.py` đạt 100% pass.
4. Đội GAME và TL thống nhất danh sách scope tính năng của game Unity được chọn để tiến hành chuyển đổi ở Sprint tiếp theo.
