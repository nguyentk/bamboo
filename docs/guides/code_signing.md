# Bamboo Engine — Hướng dẫn cấu hình ký số (Code Signing)

> Sprint `0.1.0-alpha.2` · PLT/BQ. Áp dụng cho bản phát hành editor (Windows, macOS) và cho game xuất ra Android.
> Script đóng gói macOS: [`misc/scripts/package_macos.sh`](../../misc/scripts/package_macos.sh) · Đóng gói phát hành: [`misc/scripts/package_release.py`](../../misc/scripts/package_release.py)

---

## 1. Nguyên tắc

- **Không bao giờ commit** chứng chỉ, mật khẩu hay keystore vào repo. Mọi bí mật lưu trong **GitHub Secrets** (Settings → Secrets and variables → Actions) và chỉ dùng trong workflow chạy trên nhánh được bảo vệ (`bamboo/main`, `release/*`), không chạy cho PR từ fork.
- File nhị phân (`.p12`, `.pfx`, `.keystore`) lưu dưới dạng base64 trong secret, giải mã ra thư mục tạm của runner và xóa ở cuối job.
- Export templates **không** ký: game do người dùng xuất ra được ký bằng chứng chỉ của chính họ khi export.

## 2. Danh sách GitHub Secrets

| Secret | Nền tảng | Nội dung |
| :--- | :--- | :--- |
| `WINDOWS_CERT_PFX_BASE64` | Windows | Chứng chỉ code signing (`.pfx`) mã hóa base64 |
| `WINDOWS_CERT_PASSWORD` | Windows | Mật khẩu của `.pfx` |
| `MACOS_CERT_P12_BASE64` | macOS | Chứng chỉ **Developer ID Application** (`.p12`) mã hóa base64 |
| `MACOS_CERT_PASSWORD` | macOS | Mật khẩu của `.p12` |
| `MACOS_SIGN_IDENTITY` | macOS | Ví dụ `Developer ID Application: <Tên tổ chức> (TEAMID)` |
| `APPLE_ID` / `APPLE_TEAM_ID` / `APPLE_APP_PASSWORD` | macOS | Tài khoản dùng cho `notarytool` (app-specific password) |
| `ANDROID_KEYSTORE_BASE64` | Android | Keystore phát hành (cho game dogfood / bản phát hành) |
| `ANDROID_KEYSTORE_USER` / `ANDROID_KEYSTORE_PASSWORD` | Android | Alias và mật khẩu keystore |

## 3. Windows — `signtool`

```yaml
- name: Sign Windows binaries
  if: ${{ github.ref == 'refs/heads/release/0.1' }}
  shell: pwsh
  env:
    CERT_PFX_BASE64: ${{ secrets.WINDOWS_CERT_PFX_BASE64 }}
    CERT_PASSWORD: ${{ secrets.WINDOWS_CERT_PASSWORD }}
  run: |
    $pfx = Join-Path $env:RUNNER_TEMP "bamboo.pfx"
    [IO.File]::WriteAllBytes($pfx, [Convert]::FromBase64String($env:CERT_PFX_BASE64))
    Get-ChildItem bin/bamboo.windows.*.exe | ForEach-Object {
      signtool sign /f $pfx /p $env:CERT_PASSWORD /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $_.FullName
    }
    Remove-Item $pfx
```

Kiểm tra: `signtool verify /pa bin\bamboo.windows.editor.x86_64.exe`.

## 4. macOS — `codesign` + `notarytool`

Trên runner, nhập chứng chỉ vào một keychain tạm:

```yaml
- name: Import Developer ID certificate
  env:
    CERT_P12_BASE64: ${{ secrets.MACOS_CERT_P12_BASE64 }}
    CERT_PASSWORD: ${{ secrets.MACOS_CERT_PASSWORD }}
  run: |
    KEYCHAIN="$RUNNER_TEMP/bamboo.keychain-db"
    echo "$CERT_P12_BASE64" | base64 --decode > "$RUNNER_TEMP/cert.p12"
    security create-keychain -p "" "$KEYCHAIN"
    security set-keychain-settings -lut 3600 "$KEYCHAIN"
    security unlock-keychain -p "" "$KEYCHAIN"
    security import "$RUNNER_TEMP/cert.p12" -P "$CERT_PASSWORD" -T /usr/bin/codesign -k "$KEYCHAIN"
    security set-key-partition-list -S apple-tool:,apple: -s -k "" "$KEYCHAIN"
    security list-keychains -d user -s "$KEYCHAIN" $(security list-keychains -d user | tr -d '"')
    rm "$RUNNER_TEMP/cert.p12"

- name: Package, sign and notarize
  env:
    BAMBOO_SIGN_IDENTITY: ${{ secrets.MACOS_SIGN_IDENTITY }}
    BAMBOO_NOTARY_APPLE_ID: ${{ secrets.APPLE_ID }}
    BAMBOO_NOTARY_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
    BAMBOO_NOTARY_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
  run: sh misc/scripts/package_macos.sh
```

`package_macos.sh` ký bundle với hardened runtime + entitlements `misc/dist/macos/editor.entitlements`, đóng gói `.dmg`, gửi `xcrun notarytool submit --wait`, chạy `xcrun stapler staple`, rồi kiểm tra bằng `spctl -a -vvv -t install`. Khi không có các biến trên, script ký **ad-hoc** (chạy được trên máy build, không qua Gatekeeper trên máy khác) và bỏ qua notarization.

Máy dev: lưu thông tin notarization một lần vào keychain rồi dùng `BAMBOO_NOTARY_PROFILE`:

```bash
xcrun notarytool store-credentials "bamboo-notary" --apple-id "<apple-id>" --team-id "<TEAMID>"
```

## 5. Android — keystore phát hành

- Template không ký. Game dogfood / game phát hành được ký khi export từ editor (Export → Android → Keystore → Release), hoặc qua biến môi trường khi export bằng dòng lệnh:

```bash
export GODOT_ANDROID_KEYSTORE_RELEASE_PATH=/path/to/release.keystore
```

```bash
export GODOT_ANDROID_KEYSTORE_RELEASE_USER=<alias>
```

```bash
export GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD=<password>
```

- Trên CI: giải mã `ANDROID_KEYSTORE_BASE64` ra `$RUNNER_TEMP/release.keystore`, đặt 3 biến trên, chạy `--export-release "Android"`, rồi xóa keystore.
- Debug keystore: editor tự tạo ở thư mục dữ liệu Bamboo khi export debug lần đầu.

## 6. Trạng thái hiện tại (10/2026)

| Hạng mục | Trạng thái |
| :--- | :--- |
| Script đóng gói/ký macOS | Có (`package_macos.sh`), đã chạy được ở chế độ ad-hoc trên máy dev |
| Chứng chỉ Developer ID, tài khoản notarization | **Chưa có** — cần đăng ký Apple Developer Program cho tổ chức |
| Chứng chỉ code signing Windows | **Chưa có** — cần mua chứng chỉ (OV/EV) |
| Keystore Android phát hành | **Chưa có** — tạo bằng `keytool` khi có game phát hành |
| Secrets trên GitHub | **Chưa cấu hình** |
