# Phân tích Kiến trúc Godot 4.x, So sánh Đối chuẩn với Unity 6 và Chiến lược cho Bamboo Engine

> **Phạm vi & nguồn:**
> - Phía Godot: đối chiếu trực tiếp với source code repo `bamboo` (Godot 4.8-dev) — mọi đường dẫn file là thật.
> - Phía Unity: dựa trên tài liệu công khai và hiện trạng Unity 6 / LTS tới thời điểm viết (10/2026); các tính năng Unity có thể thay đổi theo bản phát hành.
> - Điểm số ở Phần 4 là **đánh giá chuyên môn**, không phải kết quả benchmark đo đạc.
>
> Tài liệu liên quan: [ENGINE_ANALYSIS.md](ENGINE_ANALYSIS.md) · [architecture.md](architecture.md) · [Render_Architecture.md](Render_Architecture.md) · [Camera_Architecture.md](Camera_Architecture.md) · [Navigation_Architecture.md](Navigation_Architecture.md) · [Display_Architecture.md](Display_Architecture.md) · [Animation_Architecture.md](Animation_Architecture.md)

---

## Tóm tắt điều hành

- **Godot mạnh ở**: tốc độ lặp, 2D chuyên dụng, kiến trúc gọn và tự chủ mã nguồn (MIT), binary nhỏ, server/RID tách bạch dễ thay backend.
- **Godot yếu ở**: hiệu năng scripting CPU-bound (GDScript là VM thông dịch, không JIT), đồ họa 3D high-end (chưa GPU-driven, chưa virtualized geometry), hệ sinh thái SDK thương mại, console (phụ thuộc bên thứ 3), pipeline nội dung cho live-ops.
- **Unity mạnh ở**: hệ sinh thái, console/mobile SDK, Burst + Jobs + IL2CPP cho hiệu năng C#, HDRP/URP + VFX Graph, công cụ production (Timeline, Addressables, Profiler).
- **Kết luận chiến lược cho Bamboo**: không cạnh tranh trực diện với Unity/Unreal ở AAA. Định vị **"engine tự chủ, nhẹ, hiệu năng cao cho 2D / mobile mid-core / stylized 3D, có sẵn platform services và console path"** — đạt ngang hoặc vượt Unity trong phân khúc này vào cuối 2027 là khả thi; ngang toàn diện thì không.

---

## PHẦN 1: BÓC TÁCH KIẾN TRÚC CỐT LÕI

### 1.1 Scene Tree & Node (Godot) vs GameObject & Component / ECS (Unity)

| Khía cạnh | Godot | Unity (GameObject) | Unity (DOTS / Entities) |
| :--- | :--- | :--- | :--- |
| Đơn vị cơ bản | `Node` — **vừa là dữ liệu vừa là hành vi**, có kiểu riêng (`Node3D`, `RigidBody3D`, `Control`…) | `GameObject` rỗng + `Component` (`Transform` bắt buộc) | `Entity` (ID) + `IComponentData` (struct) + `System` |
| Mô hình tái sử dụng | **Kế thừa class** + **composition bằng cây con** + **scene lồng nhau** (`PackedScene` instancing, scene inheritance) | Composition component trên một GameObject + Prefab / Prefab Variant | Data-oriented, archetype chunk |
| Bố cục bộ nhớ | Object rời rạc trên heap (`memnew`), truy cập qua con trỏ; dữ liệu nặng (render/physics) nằm trong **Server** dưới dạng RID pool liên tục | Object C++ native + wrapper C# managed; Transform hierarchy được tối ưu riêng | Chunk 16 KB liên tục, SoA, cache-friendly |
| Đa luồng | `WorkerThreadPool`, Server có thể chạy thread riêng (`CommandQueueMT`), scene thread groups (`Node::process_thread_group`) | Main thread + Job System (C# Jobs, Burst) | Mặc định đa luồng qua Jobs + Burst |
| Giao tiếp | Signal / Callable, `call_deferred`, group | UnityEvent, SendMessage, C# event | Query / System ordering |

**Ưu điểm của Godot**
- **Mô hình tư duy đơn giản**: "một cảnh là một cây node"; một `.tscn` vừa là level, vừa là prefab, vừa là UI widget → học nhanh, dễ đọc.
- **Scene lồng nhau + kế thừa scene** cho phép tái sử dụng mạnh không kém Prefab Variant.
- **Tách dữ liệu nặng xuống Server qua RID** (`servers/rendering`, `servers/physics_3d`): phần render/physics đã là data-oriented ở tầng dưới, scene chỉ là "lớp mô tả".
- **Signal** là cơ chế loose-coupling có sẵn, được editor hỗ trợ kết nối trực quan.

**Nhược điểm của Godot**
- **Mỗi Node là một `Object` đầy đủ** (property list, signal map, notification, script instance) → chi phí bộ nhớ và CPU mỗi node cao; cảnh 50k–100k node chủ động xử lý (`_process`) sẽ nghẽn main thread.
- **Không có ECS chính thức**; muốn data-oriented phải tự dùng Server API trực tiếp (`RenderingServer.instance_create`, `PhysicsServer3D.body_create`) hoặc `MultiMesh`.
- **Kế thừa class + `extends` một tầng** trong GDScript dễ dẫn tới cây kế thừa sâu; composition phải làm thủ công bằng node con.
- **Streaming thế giới mở**: không có hệ chia cell/streaming chuẩn (Unity có Addressables + Scene streaming; Unreal có World Partition). Godot phải tự xây bằng `ResourceLoader.load_threaded_request` + quản lý cây thủ công.

**So sánh khả năng scale**

| Quy mô | Godot | Unity |
| :--- | :--- | :--- |
| Indie / mid-size (≤ vài nghìn entity động) | Tốt | Tốt |
| Nhiều entity động (crowd, RTS, bullet hell 3D) | Cần bypass scene, dùng Server API / MultiMesh / GDExtension | DOTS + Burst xử lý hàng trăm nghìn entity |
| Open-world | Thiếu streaming, HLOD, large-world tooling chuẩn (có `precision=double` build) | Có giải pháp (Addressables, scene streaming, Terrain), nhưng vẫn kém Unreal |
| AAA | Chưa phù hợp (thiếu pipeline đồ họa + tooling + console) | Khả thi (HDRP), dù Unreal chiếm ưu thế |

### 1.2 Kích thước Engine & Quy trình Khởi động

Số đo thực tế trên repo này (Godot 4.8-dev, build editor không dev):

| Hạng mục | Godot | Unity 6 |
| :--- | :--- | :--- |
| Editor binary | `godot.macos.editor.arm64` ≈ **124 MB**; `godot.windows.editor.x86_64.llvm.exe` ≈ **154 MB** | Editor + module nền tảng: **nhiều GB** (mỗi platform module vài trăm MB – vài GB) |
| Gói phân phối | `.dmg` ≈ 72 MB, `.zip` Windows ≈ 75 MB | Unity Hub + Editor + modules |
| Cài đặt | **Zero-install**: một file chạy, chế độ self-contained (`_sc_`) | Unity Hub, đăng nhập tài khoản, license activation |
| Mở project | Vài giây (project nhỏ); import lần đầu tỷ lệ với số asset | Thường chậm hơn đáng kể: domain reload, package resolve, asset import |
| Build engine từ source | Có (SCons, 15–60 phút); ai cũng làm được | Không (source chỉ dành cho khách hàng Enterprise/có thỏa thuận) |
| Template runtime | Có thể strip mạnh (`disable_3d`, `modules_enabled_by_default=no`, `build_profile`) → bản 2D/Web nhỏ hơn nhiều | Code stripping (IL2CPP managed stripping), engine stripping hạn chế |

**Phân tích**: kích thước nhỏ và zero-install là lợi thế thật cho iteration (CI dễ, onboarding nhanh, chạy được trên máy yếu, Android editor). Đổi lại, Godot không có package manager tầm Unity Package Manager — phụ thuộc thư viện quản lý thủ công (addons/ copy vào project).

---

## PHẦN 2: PHÂN TÍCH CHI TIẾT TỪNG PHÂN HỆ

### 2.1 Ngôn ngữ lập trình & Scripting Pipeline

**(1) Cách Godot giải quyết**
- **GDScript** (`modules/gdscript`): ngôn ngữ riêng, cú pháp Python-like, **compile sang bytecode, chạy trên VM thông dịch** (không JIT, không AOT). Typed GDScript cho phép VM dùng opcode chuyên biệt kiểu tĩnh (nhanh hơn untyped đáng kể nhưng vẫn là interpreter).
- **C# / .NET** (`modules/mono`, tắt mặc định): .NET 8, gọi engine qua binding sinh tự động. Hỗ trợ nền tảng theo `detect.py`: Windows, Linux, macOS, Android, iOS, visionOS — **không có Web** (không có `mono` trong danh sách `supported` của `platform/web/detect.py`).
- **GDExtension** (`core/extension/`): C ABI ổn định + `extension_api.json`; binding C++ (godot-cpp), Rust (gdext), Swift… Code native đầy đủ tốc độ.
- Mọi ngôn ngữ đi qua **ClassDB + Variant** — chi phí marshalling mỗi lời gọi engine.

**(2) Ưu điểm**
- GDScript tích hợp sâu vào editor (autocomplete, debugger, hot reload), **lặp cực nhanh**, không có "domain reload".
- GDExtension cho phép viết hệ thống hiệu năng cao **không cần fork engine**.
- Đa ngôn ngữ thực sự qua một ABI duy nhất.

**(3) Nhược điểm**
- **GDScript chậm cho tác vụ CPU-bound** (vòng lặp số học, pathfinding tự viết, simulation): thường chậm hơn C#/C++ một bậc độ lớn.
- **Không có tương đương Burst/Jobs**: không có compiler SIMD tự động cho code người dùng, không có job system an toàn cho script.
- C# bị giới hạn nền tảng (không Web), binding qua Variant có overhead, hai runtime (GDScript + .NET) song song làm tăng độ phức tạp.
- GDExtension đòi kỹ năng C++/Rust và build chain riêng cho mỗi platform.

**(4) So với Unity**
- Unity: C# là ngôn ngữ duy nhất; **IL2CPP** (C# → C++ AOT) cho mobile/console/web; **Burst** (subset HPC# → LLVM, SIMD) + **Jobs** cho hiệu năng gần native; đang chuyển dần sang CoreCLR hiện đại.
- Unity thua ở tốc độ lặp (domain reload, compile assembly).
- **Kết luận**: Godot thắng về iteration và tính mở; Unity thắng rõ về hiệu năng scripting CPU-bound và tính đồng nhất toolchain.

### 2.2 Phân hệ 2D

**(1) Cách Godot giải quyết**
- **2D chuyên dụng**: `CanvasItem` / `Node2D` làm việc trong không gian pixel, render qua `RendererCanvasCull` + `RendererCanvasRender` (batching), **không đi qua pipeline 3D**.
- `TileMapLayer` + `TileSet` (terrain auto-tiling, physics/navigation/occlusion layer per tile), 2D lights + normal/specular map, `LightOccluder2D`, SDF 2D (GPU) cho shadow và particle collision, Y-sort, `CanvasLayer`, `Parallax2D`.
- Vật lý 2D riêng (`modules/godot_physics_2d`), navigation 2D riêng (`modules/navigation_2d`), `Skeleton2D` + modifications (IK, jiggle), `AnimatedSprite2D`.
- Pixel-perfect: `content_scale_stretch = integer`, snap 2D transforms/vertices.

**(2) Ưu điểm**: đơn vị pixel tự nhiên, không phải xử lý camera orthographic + "units per pixel"; overhead thấp; toàn bộ editor 2D được thiết kế riêng.

**(3) Nhược điểm**: vật lý 2D chỉ có một backend (GodotPhysics2D, chưa có Box2D chính thức); thiếu công cụ animation 2D dạng bone-rig chuyên sâu như Spine (cần plugin); batching 2D có thể bị phá bởi nhiều material/texture khác nhau.

**(4) So với Unity**: Unity 2D là **3D-projected 2D** (URP 2D Renderer, Sprite, Tilemap, 2D Animation/IK package, PSD Importer, Box2D-based Physics 2D). Hệ thống trưởng thành, nhiều package; nhưng thao tác 2D vẫn mang "dư âm" 3D (Z-order, units). **Godot nhỉnh hơn về tính chuyên dụng và tốc độ làm việc 2D; Unity nhỉnh hơn ở công cụ art pipeline (PSD Importer, 2D Animation).**

### 2.3 Phân hệ 3D & Rendering Pipeline

**(1) Cách Godot giải quyết** (chi tiết: [Render_Architecture.md](Render_Architecture.md))
- 3 rendering method: **Forward+** (clustered lighting), **Mobile** (forward, tối ưu tile-based), **Compatibility** (GLES3/WebGL2).
- Backend GPU qua `RenderingDevice`: **Vulkan, Direct3D 12, Metal** (`drivers/vulkan|d3d12|metal`); `RenderingDeviceGraph` tự xử lý barrier.
- GI: **SDFGI** (real-time, cascade), **VoxelGI**, **LightmapGI** (bake GPU), SSIL, reflection probe.
- Effects: volumetric fog, SSAO/SSR, TAA, **FSR 1/2**, **MetalFX**, SMAA, DOF, glow, tonemap; `CompositorEffect` để chèn pass tùy biến.
- Repo hiện có `modules/texture_streaming` và shader baker khi export (`editor/shader/shader_baker/`).

**(2) Ưu điểm**: kiến trúc sạch, một API GPU nội bộ cho 3 backend; GI real-time "bật là chạy" (SDFGI) cho indie; Compatibility giúp chạy trên phần cứng rất cũ và Web.

**(3) Nhược điểm**
- **CPU-driven**: chưa có GPU-driven culling/indirect draw, chưa có meshlet/virtualized geometry → giới hạn số object/draw call.
- SDFGI có leak ánh sáng và chi phí cao; chưa có probe volume tự động kiểu APV.
- Chưa có node-based **VFX tương đương VFX Graph** (GPUParticles + particle shader là đủ nhưng kém tooling).
- Visual Shader tồn tại nhưng hệ sinh thái shader thua Shader Graph + Asset Store.
- **Web chỉ có WebGL2** (Compatibility); không có WebGPU.
- Thiếu dynamic resolution tự động, chưa có upscaler tích hợp sẵn DLSS/XeSS.

**(4) So với Unity**: Unity 6 có **URP** (scalable, mobile→PC) và **HDRP** (high-end), **Render Graph**, **GPU Resident Drawer** (GPU instancing/culling tự động cho GameObject), **Adaptive Probe Volumes (APV)**, **STP** upscaler, **Shader Graph**, **VFX Graph** (GPU, hàng triệu particle), WebGPU (đang phát triển). *Lưu ý: "Virtual Shadow Maps" là tính năng của Unreal Engine, không phải Unity; Unity HDRP có shadow caching / cascade, không phải VSM.* **Unity vượt Godot rõ rệt ở 3D high-end và scalability; Godot đủ tốt cho stylized/mid-fidelity.**

### 2.4 Hệ thống Vật lý

**(1) Cách Godot giải quyết**
- Kiến trúc server: `PhysicsServer2D/3D` + `PhysicsServer3DManager` chọn backend qua project setting `physics/3d/physics_engine`.
- **Jolt Physics đã là module tích hợp sẵn trong core** (`modules/jolt_physics`, Jolt 5.6.0) — *không còn chỉ là GDExtension cộng đồng*. Ở mức engine, backend mặc định đăng ký vẫn là GodotPhysics3D (`modules/godot_physics_3d/register_types.cpp:58`), người dùng chọn Jolt trong Project Settings.
- 2D: chỉ GodotPhysics2D.
- Ragdoll (`PhysicalBoneSimulator3D`), SoftBody3D, character controller (`CharacterBody2D/3D` kinematic + `move_and_slide`).

**(2) Ưu điểm**: thay backend không cần sửa scene; Jolt mang lại hiệu năng và ổn định tốt cho 3D; `CharacterBody` dễ dùng.

**(3) Nhược điểm**: GodotPhysics3D kém ổn định với stacking/joint phức tạp; vật lý 2D không có lựa chọn thay thế; không có physics determinism cross-platform chính thức (cần cho rollback netcode); không có vehicle/cloth chất lượng cao sẵn.

**(4) So với Unity**: Unity dùng **PhysX** cho GameObject (ổn định, quen thuộc), **Unity Physics** (stateless, deterministic) và **Havok Physics for Unity** cho DOTS; 2D dùng Box2D. **Với Jolt tích hợp, khoảng cách 3D đã thu hẹp đáng kể; Unity còn hơn ở lựa chọn deterministic (Unity Physics) và Havok cho quy mô lớn.**

### 2.5 Giao diện Người dùng (UI)

**(1) Cách Godot giải quyết**: `Control` node + `Container` (layout tự động: VBox/HBox/Grid/Flow/Margin…) + `Theme` (StyleBox, font, constant, theme variation). Text qua `TextServer` (HarfBuzz/ICU — BiDi, shaping đầy đủ), `RichTextLabel` (BBCode), accessibility qua AccessKit (`drivers/accesskit`). **Chính editor Godot được dựng bằng hệ UI này** → được kiểm chứng ở quy mô rất lớn.

**(2) Ưu điểm**: một hệ UI cho cả game và tool; layout container mạnh; i18n/BiDi tốt; hỗ trợ screen reader (hiếm có ở game engine).

**(3) Nhược điểm**: không có tách biệt markup/style kiểu web (UXML/USS); data binding chưa có chuẩn; hiệu năng UI rất phức tạp (hàng nghìn Control) cần tối ưu thủ công; theme editing chưa thân thiện với UI artist.

**(4) So với Unity**: Unity có **UGUI** (GameObject-based, trưởng thành, nhiều asset) và **UI Toolkit** (**UXML + USS**, retained-mode, data binding runtime, dùng cho cả editor). UI Toolkit tiến bộ hơn về tách style/logic; UGUI có hệ sinh thái lớn hơn. **Godot UI vượt UGUI về layout và text, kém UI Toolkit về mô hình markup/style và data binding.**

### 2.6 Animation & Audio Pipeline

**Animation** (chi tiết: [Animation_Architecture.md](Animation_Architecture.md))
- **(1) Godot**: `AnimationPlayer` (track cho **bất kỳ property nào**, method, audio, bezier), `AnimationTree` (BlendTree, StateMachine, BlendSpace 1D/2D, OneShot, Transition), `AnimationMixer` chung; nhiều `SkeletonModifier3D` (TwoBone/CCD/FABRIK/Jacobian/Spline IK, LookAt, SpringBone, Retarget); retarget humanoid qua `SkeletonProfile` + `BoneMap`; `Tween`.
- **(2) Ưu điểm**: "animate mọi thứ" (UI, shader, material) bằng một hệ; modifier không phá hủy pose; IK và spring bone có sẵn.
- **(3) Nhược điểm**: không có **Timeline/Sequencer** chuyên cho cutscene (dựng bằng AnimationPlayer lồng nhau); không có inertialization, motion matching, animation LOD, GPU crowd.
- **(4) Unity**: Mecanim (state machine, avatar humanoid retarget tự động — trưởng thành hơn), **Timeline** (sequencer đa track, Cinemachine tích hợp), Animation Rigging package. **Unity hơn ở cutscene/cinematic pipeline; Godot hơn ở tính tổng quát và IK có sẵn.**

**Audio**
- **(1) Godot**: `AudioServer` với **bus layout + effect chain** (reverb, compressor, EQ, limiter, chorus…), `AudioStreamPlayer/2D/3D`, Ogg Vorbis / MP3 / WAV; `modules/interactive_music` có `AudioStreamInteractive` (chuyển nhạc theo clip/transition), `AudioStreamPlaylist`, `AudioStreamSynchronized` (layer đồng bộ).
- **(2) Ưu điểm**: adaptive music cơ bản có sẵn — Unity cần middleware cho việc này.
- **(3) Nhược điểm**: spatial audio cơ bản (không HRTF/occlusion chuẩn), không có integration chính thức FMOD/Wwise (cộng đồng có plugin GDExtension), profiling audio hạn chế.
- **(4) Unity**: `AudioMixer` (snapshot, group, effect), spatializer plugin SDK, FMOD/Wwise có integration chính thức từ vendor. **Unity hơn ở middleware ecosystem; Godot hơn ở adaptive music built-in.**

---

## PHẦN 3: HỆ SINH THÁI, PLATFORM & XUẤT BẢN

### 3.1 Multi-platform & Console

| Nền tảng | Godot 4.x | Unity 6 |
| :--- | :--- | :--- |
| Windows / Linux / macOS | Tốt (Vulkan, D3D12, Metal, GL) | Tốt |
| Android / iOS | Tốt (Vulkan/Metal/GLES3); C# trên mobile còn non | Rất tốt; tối ưu và SDK đầy đủ |
| visionOS / XR | Có (`platform/visionos`, OpenXR, WebXR) | Rất tốt (PolySpatial, XR Interaction Toolkit) |
| Web | WebGL2 + WASM; thread cần SharedArrayBuffer (COOP/COEP); **không C#**; không WebGPU | WebGL2 + WASM, IL2CPP; WebGPU đang phát triển |
| Console (PS5, Xbox, Switch/Switch 2) | **Không có trong source mở**; port qua bên thứ 3 (W4 Games, Pineapple Works, Lone Wolf Technology…) | Hỗ trợ chính thức qua platform module sau khi được nhà sản xuất console cấp quyền dev |

**Vấn đề console — bản chất kỹ thuật & pháp lý**
- MIT **không cấm** dùng SDK đóng; rào cản là **SDK console nằm dưới NDA** nên code tích hợp **không thể công bố công khai** trong repo MIT. Vì vậy port console phải tồn tại dưới dạng nhánh đóng do bên có quyền NDA duy trì.
- Hệ quả: phí dịch vụ port, độ trễ cập nhật theo phiên bản engine, phụ thuộc vào đối tác.
- Unity: không phải "1-click" thực sự (vẫn cần đăng ký developer với Sony/Microsoft/Nintendo, devkit, certification), nhưng **platform module chính thức + tài liệu + hỗ trợ** làm chi phí gần như bằng 0 về engine.
- **Với Bamboo**: kiến trúc `platform/<name>/` + `RenderingDeviceDriver` + `DisplayServer` cho phép thêm console như một platform; cần **một nhánh private** dưới NDA và đối tác/tài nguyên riêng.

### 3.2 Chợ tài nguyên & Cộng đồng

| Khía cạnh | Godot AssetLib | Unity Asset Store |
| :--- | :--- | :--- |
| Mô hình | Miễn phí, mã nguồn mở, không có thanh toán | Thương mại + miễn phí, có marketplace |
| Quy mô | Nhỏ (chủ yếu tool, script, shader) | Rất lớn (art, tool, template, SDK) |
| SDK quảng cáo / IAP / analytics | Phần lớn do cộng đồng (plugin Android/iOS, GDExtension), mức bảo trì không đều | **SDK chính thức từ vendor** (AdMob, AppLovin MAX, IronSource/LevelPlay, Firebase, GameAnalytics…) + Unity Gaming Services (Analytics, Remote Config, Cloud Save, Economy, Relay/Lobby) |
| Live-ops / content delivery | Không có giải pháp chuẩn (PCK patching tự làm) | Addressables + CCD, Remote Config |
| Rủi ro phụ thuộc | Thấp (mọi thứ mở) | Phụ thuộc chính sách vendor (ví dụ sự kiện Runtime Fee 2023, đã hủy năm 2024) |

**Kết luận**: đây là **khoảng cách lớn nhất** giữa Godot và Unity cho game thương mại mobile/live-service — không phải engine core mà là **SDK + dịch vụ**.

---

## PHẦN 4: MA TRẬN SO SÁNH TỔNG HỢP

Thang điểm 1–10, đánh giá chuyên môn tại thời điểm 10/2026.

| Tiêu chí | Godot 4.x | Unity 6 / LTS | Nhận xét kiến trúc |
| :--- | :---: | :---: | :--- |
| Tốc độ lặp (Iteration / Startup) | **9** | 6 | Godot: binary ~124–154 MB, zero-install, không domain reload, GDScript hot reload. Unity: domain reload, package resolve, compile assembly làm chậm vòng lặp |
| Game 2D thuần | **9** | 8 | Godot có canvas pipeline pixel-space riêng, TileMapLayer, physics/navigation 2D riêng. Unity 2D trưởng thành, art tool tốt hơn nhưng là 3D-projected |
| Đồ họa 3D high-end (Fidelity / Scalability) | 6 | **8** | Godot: Forward+ CPU-driven, SDFGI. Unity: HDRP, GPU Resident Drawer, APV, VFX Graph. (Cả hai đều sau Unreal) |
| Hiệu năng scripting CPU-intensive | 5 | **9** | GDScript là bytecode VM không JIT; C#/GDExtension cải thiện nhưng không có Burst/Jobs. Unity: IL2CPP + Burst SIMD + Jobs |
| Độ ổn định trên diện rộng | 7 | **8** | Godot ít regression lớn nhưng ít được kiểm chứng ở dự án lớn/console; Unity kiểm chứng ở hàng chục nghìn game thương mại, dù cũng có regression |
| Asset Store & SDK bên thứ 3 | 4 | **10** | Khoảng cách hệ sinh thái: ads, analytics, IAP, backend, middleware audio |
| Tự chủ mã nguồn & giấy phép | **10** | 4 | Godot MIT, full source, không phí; Unity: source chỉ qua thỏa thuận đặc biệt, phụ thuộc chính sách giá |
| Xuất bản console | 4 | **10** | Godot qua bên thứ 3 dưới NDA; Unity có platform module chính thức |

---

## PHẦN 5: ĐỊNH HƯỚNG CHIẾN LƯỢC CHO BAMBOO ENGINE

Định vị đề xuất: **"Godot-compatible, production-ready engine cho 2D, mobile mid-core và stylized 3D — tự chủ mã nguồn, có sẵn platform services và đường đi console."** Giữ tương thích project Godot (định dạng `.tscn/.tres/project.godot`, GDExtension ABI) để thừa hưởng cộng đồng; cạnh tranh bằng những thứ Godot upstream chậm làm.

### Chiến lược 1 — Hiệu năng scripting & runtime (đóng khoảng cách Burst/IL2CPP)
- **Typed GDScript AOT khi export**: transpile GDScript có kiểu tĩnh sang C++ (biên dịch thành GDExtension nội bộ) cho bản release; editor vẫn dùng VM để giữ iteration.
- **Bamboo Jobs API**: expose `WorkerThreadPool` cho script/C# với kiểu dữ liệu packed (PackedFloat32Array, typed struct) để chạy song song an toàn.
- **Data-oriented layer tùy chọn**: `BmEntityWorld` dựa trên Server API (RID) cho crowd/bullet/RTS — không thay scene tree, bổ sung cho nó.
- KPI: script benchmark CPU-bound đạt ≥ 5× GDScript typed hiện tại; 50k entity động ở 60 FPS trên PC tầm trung.

### Chiến lược 2 — Mobile-first rendering & performance
- Tối ưu **Mobile renderer** trên Vulkan Android: pipeline cache/PSO precompile bằng shader baker, giảm stutter lần đầu; frame pacing (Swappy đã có); thermal-aware **dynamic resolution** ([Display_Architecture.md](Display_Architecture.md)).
- Bật và hoàn thiện `modules/texture_streaming`, ASTC/ETC2 pipeline, mesh LOD tự động (meshoptimizer).
- **Animation LOD + GPU skinning crowd** ([Animation_Architecture.md](Animation_Architecture.md)).
- KPI: game mid-core 3D chạy ổn định 60 FPS / 30 FPS trên thiết bị Android tầm trung (Adreno 6xx / Mali-G7x), không stutter shader sau lần chạy đầu.

### Chiến lược 3 — Platform Services Layer & SDK chính thức (đóng khoảng cách hệ sinh thái)
- **Bamboo Services API thống nhất** (GDExtension + plugin Android/iOS bảo trì chính thức): Ads mediation, IAP (Google Play Billing, StoreKit 2), Analytics, Push, Remote Config, Crash reporting, Cloud Save, Auth.
- **Content delivery**: hệ bundle/PCK theo nhóm (kiểu Addressables) + patch delta + CDN → nền tảng cho live-ops.
- KPI: một game mobile F2P tích hợp đủ monetization + analytics trong ≤ 1 tuần.

### Chiến lược 4 — Pipeline nội dung & tooling production
- **Asset pipeline**: import song song, **import cache server** dùng chung cho team/CI, deterministic import.
- **Timeline/Sequencer + Virtual Camera** ([Camera_Architecture.md](Camera_Architecture.md)) cho cutscene.
- **Profiler hợp nhất** (CPU zone Tracy/Perfetto + GPU timestamp + memory) trong editor.
- KPI: thời gian import lại project 10 GB giảm ≥ 50% khi có cache server.

### Chiến lược 5 — Đường đi Console & WebGPU
- **Console**: lập nhánh private dưới NDA, xây `platform/<console>` + `RenderingDeviceDriver` (GNM/AGC, NVN, D3D12 GDK) + `DisplayServer` tối thiểu; ưu tiên Switch (phù hợp phân khúc 2D/stylized). Phương án thay thế: hợp tác với đơn vị port có sẵn.
- **WebGPU backend** cho `RenderingDevice` → đưa Mobile renderer lên Web (thay WebGL2) và mở đường C# qua WASM.
- KPI: một game mẫu qua lotcheck/certification trên ít nhất 1 console; demo Mobile renderer chạy trên WebGPU ở Chrome.

---

## PHẦN 6: ROADMAP PHÁT TRIỂN BAMBOO ENGINE ĐẾN CUỐI 2027

### Giả định nguồn lực
- **Đội lõi ~10–14 kỹ sư**: 3 rendering, 2 runtime/scripting, 2 platform/mobile, 2 tools/editor, 1–2 services/backend, 1 build/QA/CI, 1 tech lead/PM. Kèm 1–2 game nội bộ dùng thử (dogfooding).
- Console phụ thuộc thời gian được cấp quyền developer từ nhà sản xuất console (thường vài tháng) — cần nộp hồ sơ ngay Q4/2026.
- Nhịp rebase upstream Godot mỗi bản minor (≈ 4–6 tháng một lần).

### Mục tiêu "ngang Top 2" cuối 2027 — định nghĩa có thể đo được
| Phân khúc | Mục tiêu |
| :--- | :--- |
| 2D (mọi thể loại) | Ngang hoặc hơn Unity về tính năng + iteration; có Spine-like 2D rig hoặc integration chính thức |
| Mobile mid-core 2D/3D | Ngang Unity URP về hiệu năng trên Android/iOS tầm trung; SDK monetization đầy đủ |
| Stylized 3D PC/console | Đủ để ship trên PC + ít nhất 1 console |
| AAA photorealistic | **Không phải mục tiêu** đến 2027 |

### Q4/2026 — Nền móng (Foundation)
**Mục tiêu**: fork ổn định, quy trình chuyên nghiệp, đo được hiệu năng.
- Hoàn tất rebranding (Phase 1–5 đã làm) + icon/logo; build editor/template cho Win/macOS/Linux/Android/iOS/Web trên CI.
- CI matrix + **golden-image rendering tests** + benchmark suite (CPU script, draw call, physics, startup time) chạy hàng đêm.
- Quy trình rebase upstream (`// BAMBOO:` tags, commit theo tính năng), `custom_modules` repo `bamboo_modules`.
- Bật Jolt làm mặc định cho project mới; preset build profile cho 2D / Mobile / PC.
- Nộp hồ sơ developer console (Nintendo trước).
- **Exit criteria**: build xanh mọi nền tảng; dashboard benchmark baseline; 1 game nội bộ chạy trên Bamboo.

### Q1/2027 — Mobile & Performance I
- Shader/PSO precompile + warm-up; frame pacing; **dynamic resolution** theo GPU time; thermal throttling handling.
- Texture streaming production-ready; ASTC pipeline; animation LOD (`BmAnimationLOD`).
- `BmDisplaySettings`, `BmSafeAreaContainer` ([Display_Architecture.md](Display_Architecture.md)).
- Bắt đầu **Bamboo Services v0**: IAP (Play Billing/StoreKit 2) + Analytics + Crash reporting.
- **Exit criteria**: game mẫu 3D mid-core đạt 60 FPS ổn định trên Android tầm trung, 0 shader stutter sau lần chạy đầu; IAP chạy thật trên 2 store.

### Q2/2027 — Scripting & Runtime
- **Typed GDScript AOT (alpha)** cho release export; Bamboo Jobs API cho script.
- `BmEntityWorld` (data-oriented layer trên Server API) cho crowd/bullet.
- Path scheduler + nav tile rebake ([Navigation_Architecture.md](Navigation_Architecture.md)).
- Services v1: Ads mediation, Remote Config, Cloud Save.
- Console: dựng `platform/<console>` skeleton trong nhánh private (sau khi có devkit).
- **Exit criteria**: benchmark CPU-bound ≥ 3× typed GDScript; 50k entity demo 60 FPS PC; game F2P mẫu tích hợp đủ ads + IAP + analytics.

### Q3/2027 — Tooling & Content Pipeline
- **Timeline/Sequencer** + **Virtual Camera System** (`BmCameraBrain`, shake/impulse, `camera_cut()`).
- Content bundles + delta patch + CDN (live-ops), import cache server.
- Profiler hợp nhất (Tracy/Perfetto + GPU + memory) trong editor.
- GDScript AOT beta (mục tiêu ≥ 5×); inertialization + foot IK ([Animation_Architecture.md](Animation_Architecture.md)).
- Console: game mẫu chạy trên devkit; `RenderingDeviceDriver` console hoàn thiện cơ bản.
- **WebGPU backend (prototype)**.
- **Exit criteria**: cutscene sản xuất được hoàn toàn trong editor; patch nội dung không cần cập nhật store; game mẫu chạy trên console devkit.

### Q4/2027 — Production Ready 1.0
- **Bamboo 1.0 LTS**: đóng băng API, chính sách hỗ trợ dài hạn, tài liệu đầy đủ, template dự án theo thể loại (2D platformer, mobile F2P, stylized 3D action).
- Console: nộp certification cho game mẫu / game đối tác đầu tiên.
- WebGPU beta (Mobile renderer trên Web).
- GPU-driven culling (giai đoạn 1) cho Forward+/Mobile; DLSS/XeSS qua `SpatialUpscaler`.
- Marketplace/registry plugin Bamboo (có kiểm định tương thích phiên bản).
- **Exit criteria**: ≥ 2 game thương mại (nội bộ hoặc đối tác) phát hành trên Bamboo; ma trận Phần 4 cải thiện tối thiểu: Scripting 5→8, 3D 6→7, SDK 4→7, Console 4→7.

### Tổng quan roadmap

| Quý | Trọng tâm | Chiến lược | Kết quả then chốt |
| :--- | :--- | :--- | :--- |
| Q4/2026 | Nền móng | — | Fork + CI + benchmark + hồ sơ console |
| Q1/2027 | Mobile & Performance I | 2, 3 | 60 FPS mobile mid-core, IAP + analytics |
| Q2/2027 | Scripting & Runtime | 1, 3, 5 | GDScript AOT alpha, Jobs, ads mediation |
| Q3/2027 | Tooling & Content | 4, 5 | Timeline, Virtual Camera, live-ops, console devkit |
| Q4/2027 | Bamboo 1.0 LTS | 1–5 | 2 game thương mại, console cert, WebGPU beta |

### Rủi ro chính & biện pháp

| Rủi ro | Tác động | Biện pháp |
| :--- | :--- | :--- |
| Lệch xa upstream Godot, rebase tốn kém | Cao | Ưu tiên module/GDExtension; patch lõi nhỏ, gắn tag; rebase theo nhịp cố định |
| Chậm được cấp quyền console | Cao | Nộp hồ sơ sớm; phương án hợp tác đơn vị port có sẵn |
| GDScript AOT phức tạp hơn dự kiến | Trung bình | Bắt đầu với subset typed; fallback C#/GDExtension cho hot path |
| Thiếu nhân lực SDK/services | Trung bình | Ưu tiên SDK theo nhu cầu game nội bộ; dùng SDK vendor qua plugin mỏng |
| Mất tương thích với hệ sinh thái Godot | Trung bình | Giữ định dạng project và GDExtension ABI; CI chạy bộ project Godot mẫu |
