# TASK [BQ]: Đóng Gói Bản Cài Đặt Chính Thức, Ký Số & Apple Notarization

> **Agent**: `BQ` (Build & CI)  
> **Milestone**: `0.1.0` (Tuần 9 · 07/12 – 11/12/2026)  
> **Mục tiêu**: Tự động hóa quy trình đóng gói bản phát hành chính thức (`.dmg` cho macOS, `.zip` cho Windows/Linux, `.tpz` cho export templates); thực hiện ký số và Apple Notarization; viết unit test kiểm tra tính toàn vẹn của artifacts.

---

## 1. Bối cảnh & Tech Stack
Để người dùng và đối tác có thể mở Bamboo Engine trên macOS và Windows mà không bị hệ điều hành chặn cảnh báo bảo mật (SmartScreen hoặc Gatekeeper "damaged app"):
- **macOS**: Ứng dụng phải được ký bằng chứng chỉ Apple Developer ID, đính kèm entitlements (hardened runtime), đóng gói thành `.dmg` và gửi lên Apple Notary Service (`xcrun notarytool`) để dán tem hợp lệ (`xcrun stapler`).
- **Windows**: Binary `.exe` phải được ký số qua `signtool.exe`.
- **Export Templates**: Gói `.tpz` hoàn chỉnh gom đầy đủ cả 6 nền tảng.

---

## 2. Nhiệm vụ Chi tiết

### Bước 1: Kịch Bản Đóng Gói macOS & Notarization (`misc/scripts/package_macos.sh`)
Viết script tự động:
1. Ký binary và bundle `.app`:
   ```bash
   codesign --force --timestamp --options runtime \
            --sign "Developer ID Application: Bamboo Team" \
            --entitlements misc/dist/macos/editor.entitlements \
            bin/Bamboo.app
   ```
2. Đóng gói file `.dmg` qua `create-dmg` hoặc `hdiutil`.
3. Gửi công chứng qua Notary API:
   ```bash
   xcrun notarytool submit bin/Bamboo_v0.1.0_macOS.dmg \
         --keychain-profile "bamboo-notary" --wait
   xcrun stapler staple bin/Bamboo_v0.1.0_macOS.dmg
   ```
4. Kiểm tra hợp lệ bằng lệnh Gatekeeper:
   ```bash
   spctl -a -vvv -t install bin/Bamboo_v0.1.0_macOS.dmg
   ```

### Bước 2: Đóng Gói Bản Windows & Linux
- Windows: Đóng gói `Bamboo_v0.1.0_win64.zip` chứa `bamboo.exe` đã ký số.
- Linux: Đóng gói `Bamboo_v0.1.0_linux.x86_64.tar.xz`.
- Export Templates: Đóng gói `Bamboo_v0.1.0_export_templates.tpz`.

### Bước 3: Sinh Bảng Mã Băm SHA-256 (`SHA256SUMS.txt`)
Tự động tính mã băm cho toàn bộ các file thành phẩm để người dùng kiểm tra toàn vẹn khi tải về:
```bash
sha256sum bin/Bamboo_v0.1.0_* > bin/SHA256SUMS.txt
```

### Bước 4: Viết Unit Test Kiểm Tra Artifacts Phát Hành (`tests/python_build/test_release_artifacts.py`)
Tạo unit test Python:
- Kiểm tra sự tồn tại của tất cả các file trong danh sách phát hành.
- Kiểm tra dung lượng file nằm trong ngưỡng tiêu chuẩn (vd: `.dmg` $\ge 50$ MB và $\le 150$ MB).
- Tính toán lại mã băm SHA-256 và so khớp 100% với file `SHA256SUMS.txt`.

---

## 3. Lệnh Thực Thi & Kiểm Chứng

```bash
# 1. Chạy test Python kiểm tra toàn vẹn gói phát hành
python3 -m unittest tests/python_build/test_release_artifacts.py

# 2. Kiểm tra Gatekeeper trên file DMG thành phẩm
spctl -a -vvv -t install bin/Bamboo_v0.1.0_macOS.dmg
```

---

## 4. Tiêu chí Nghiệm thu (Exit Criteria / Definition of Done)
1. File `.dmg` trên macOS được công chứng thành công (Gatekeeper đánh giá "source=Notarized Developer ID").
2. Bộ artifact đầy đủ (.dmg, .zip Windows, .tar.xz Linux, .tpz templates) sẵn sàng trong thư mục `bin/`.
3. File test `tests/python_build/test_release_artifacts.py` pass 100%.
4. File `SHA256SUMS.txt` được tạo đầy đủ.
