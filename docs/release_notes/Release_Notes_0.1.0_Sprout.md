# Bamboo Engine 0.1.0 "Sprout" — Release Notes

> **BẢN NHÁP (DRAFT)** — chưa phát hành. Phiên bản hiện tại trong `version.py`: `0.1.0-alpha.1`.
> Ngày phát hành dự kiến: 18/12/2026 (sau Go/No-go 17/12). Kiểm tra điều kiện: `python3 misc/scripts/release_readiness.py --final`.
> Các mục đánh dấu ⏳ chưa đạt tại thời điểm viết nháp.

## Giới thiệu

Bamboo Engine là engine game mã nguồn mở dựa trên **Godot Engine 4.8** (giấy phép MIT). Dòng 0.1 "Sprout" (Măng) là giai đoạn nền móng: tách thương hiệu, quy trình build/kiểm thử chuyên nghiệp, và các công cụ để chuyển dự án từ Unity sang Bamboo. Project và GDExtension của Godot 4.x tiếp tục hoạt động.

## Điểm nổi bật

- **Dual-versioning bảo toàn GDExtension ABI** — phiên bản sản phẩm `0.1.0` song song với phiên bản Godot gốc `4.8`; `Engine.get_version_info()` có thêm các khóa `bamboo_*`; singleton `BambooCore` (module `bamboo_modules/bamboo_core`).
- **Jolt Physics mặc định cho project mới**; project cũ giữ engine đã cấu hình; cảnh báo rõ ràng khi engine vật lý được yêu cầu không có trong bản build.
- **3 build profile** (`profiles/`): 2D, Mobile, PC — template release macOS arm64: 58.9 MB (đầy đủ), 48.9 MB (2D, −17%), 47.8 MB (Mobile, −19%). Biến thể 2D tối giản (`optimize=size`, text server fallback, `deprecated=no`): 39.1 MB (−33.6%).
- **Thư mục dữ liệu riêng** (`~/Library/Application Support/Bamboo`, `%APPDATA%\Bamboo`, `~/.local/share/bamboo`) — không đụng tới Godot cài sẵn.
- **Công cụ chuyển đổi Unity** (`tools/unity_importer/`): khảo sát dự án, chuyển material (`.mat` → `.tres`), prefab → scene (`.tscn`) với chuyển hệ tọa độ; hướng dẫn [Unity → Bamboo](../unity_port/Unity_to_Bamboo_Migration_Guide.md).
- **Chất lượng**: benchmark suite 6 kịch bản có baseline, golden-image test cho Forward+/Mobile/Compatibility, kiểm kê patch `// BAMBOO:` 100%, CI desktop/mobile/web với `BUILD_NAME=bamboo`.

## Thay đổi so với Godot 4.8-dev

| Hạng mục | Thay đổi |
| :--- | :--- |
| Thương hiệu | Tên "Bamboo Engine", binary `bamboo.*`, hộp thoại About ghi nhận Godot, giấy phép MIT cập nhật |
| Editor | Chuỗi giao diện Bamboo; thanh trạng thái hiển thị `v0.1.0 (Sprout)` |
| Physics | Cảnh báo khi engine vật lý 3D không khả dụng (`servers/physics_3d/physics_server_3d_manager.cpp`) |
| Bản dịch | `editor/translations/editor.pot` sinh lại; sửa 3 bản dịch tiếng Việt sai placeholder |
| Build | `env.binary_prefix`, profile build, script đóng gói `.tpz`/`.dmg`/release |

## Cài đặt

1. Tải gói cho hệ điều hành của bạn và kiểm tra checksum trong `SHA256SUMS.txt`.
2. macOS (universal: Apple Silicon + Intel): mở `Bamboo_v0.1.0_macOS.dmg`, kéo Bamboo vào Applications. ⏳ Bản `.dmg` chưa được Apple notarize (cần chứng chỉ Developer ID).
3. Windows (64-bit): chạy `Bamboo_v0.1.0_win64_setup.exe` (cài cho người dùng hiện tại, không cần quyền admin; có trình gỡ cài đặt, giữ nguyên dữ liệu trong `%APPDATA%\Bamboo`), hoặc giải nén bản portable `Bamboo_v0.1.0_win64.zip`. ⏳ Bộ cài chưa ký Authenticode nên SmartScreen sẽ cảnh báo.
4. Linux: giải nén `Bamboo_v0.1.0_linux.x86_64.tar.xz`, chạy `bamboo.linuxbsd.editor.x86_64`.
5. Export templates: Editor → Manage Export Templates → Install From File → `Bamboo_v0.1.0_export_templates.tpz`.

## Hạn chế đã biết

- ⏳ Chưa có bản build Android và Web trong gói phát hành (CI đã cấu hình; chưa chạy).
- ⏳ Chưa port game Unity nội bộ thực tế (pipeline đã được kiểm chứng trên dự án mẫu `game_dogfood/`).
- Export templates không tải được từ máy chủ Godot; dùng file `.tpz` của Bamboo.
- C# không xuất được lên Web (giới hạn của Godot 4.x).

## Ghi nhận

Bamboo Engine is based on Godot Engine (https://godotengine.org). Cảm ơn cộng đồng Godot Engine contributors.
