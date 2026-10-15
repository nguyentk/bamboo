# Bamboo Q4/2026 — Trạng thái thực hiện các prompt `.prompts/` (cập nhật 15/10/2026, rc.1)

> Tổng hợp kết quả thực hiện các task trong `.prompts/0.1.0-alpha.1` → `.prompts/0.1.0`, đối chiếu từng tiêu chí DoD với bằng chứng thật.
> Môi trường: macOS (Apple M4), Xcode/Apple Clang 21, SCons 4.11. Ký hiệu: ✅ đạt · ⚠️ đạt một phần · ⛔ chưa làm được (thiếu tài nguyên/quyền) · ⏸ cố ý chưa làm (mốc phát hành).

## Tổng quan kiểm thử

| Bộ test | Kết quả |
| :--- | :--- |
| C++ doctest toàn bộ (`--test`) | 1436/1436 test case, 424 353 assertion pass (gồm `[Regression]` 1/1) |
| `[BambooVersion]` / `[JoltPhysics]` | 5/5, 3/3 |
| Python tooling (`tests/python_build`) | 190 test pass; các test cần binary/release (`BAMBOO_BINARY`, `BAMBOO_RELEASE_DIR`) 46/46 pass; còn skip: PyYAML, GUI, GitHub live |
| GDScript dogfood (`game_dogfood/tests`) | gameplay 11/11, crash reporter 8/8 |
| Golden image (11 ảnh, 3 renderer) | 0.000% khác biệt giữa 2 lần chạy |
| Smoke test | editor, `Bamboo.app`, template_debug, template_release, template `2d_min`: PASS |
| Kiểm kê patch `// BAMBOO:` | 91/91 (100%) |

## Sprint 1 — `0.1.0-alpha.1`

| Task / DoD | Trạng thái | Bằng chứng |
| :--- | :---: | :--- |
| TL: `check_dev_env.py` + test, onboarding, nhánh, nhãn | ✅ | Script phát hiện đúng 2 vấn đề thật của máy dev; `docs/Guides.md` §13; remote `upstream` (push bị chặn), nhánh `bamboo/main` local |
| TL: tạo nhãn trên GitHub | ⏸ | `misc/scripts/setup_github_labels.sh` sẵn sàng; chưa chạy (thay đổi repo GitHub, cần xác nhận + `gh`) |
| TLS: test C++ versioning, nút phiên bản `v0.1.0-alpha.1 (Sprout)` | ✅ | `tests/core/config/test_bamboo_version.cpp` |
| BQ: CI desktop (`BUILD_NAME=bamboo`, `engine_update_check=no`, smoke) | ⚠️ | Workflow đã sửa và YAML hợp lệ; **chưa chạy trên GitHub** (cần push) |
| BQ: `.tpz` + test, smoke test | ✅ | `bin/Bamboo_v0.1.0-alpha.1_templates.tpz` (macOS); dùng để export thật game dogfood |
| GAME: khảo sát Unity, mapping spec, schema + test | ⚠️ | Spec/schema/công cụ khảo sát xong; **không có dự án Unity nội bộ** để khảo sát |
| Tag `bamboo-v0.1.0-alpha.1` | ⏸ | Chờ CI xanh và commit |

## Sprint 2 — `0.1.0-alpha.2`

| Task / DoD | Trạng thái | Bằng chứng |
| :--- | :---: | :--- |
| PLT: workflow Android (arm32/arm64/x86_64), iOS (+simulator), Web (threads/no-threads, cache emsdk) + test | ⚠️ | Test 12/12 + YAML parse; **iOS device + simulator build thành công tại máy**; Android (cần NDK 29, máy có 20/21) và Web (không có Emscripten) chưa build |
| PLT: tài liệu ký số | ✅ | `docs/guides/code_signing.md` (chưa có chứng chỉ thật) |
| RT/RND: benchmark 6 kịch bản, JSON, baseline, phát hiện hồi quy | ✅ | `benchmarks/`, `benchmarks/baseline.json`; sửa giới hạn 144 FPS headless; ngưỡng theo từng chỉ số (nhiễu thật > 5%) |
| RND: golden image 3 renderer, so sánh ảnh + test | ✅ | 4 scene, 11 ảnh baseline (Metal/OpenGL trên macOS); Linux llvmpipe chưa chạy |
| GAME: `mat_converter.py`, `prefab_to_tscn.py` + test | ✅ | 18 test, file sinh ra nạp được trong engine |
| GAME: chuyển asset game Unity thật | ⛔ | Không có dự án Unity |
| RT/RND: nightly CI benchmark + golden image (Linux llvmpipe, macOS) | ⚠️ | `.github/workflows/bamboo_nightly.yml` + test; baseline riêng từng runner, lần chạy đầu tự ghi baseline (chưa chạy — cần push) |
| Baseline benchmark cho build `0.1.0-alpha.2` | ✅ | `benchmarks/baseline.json` (`bamboo_version: 0.1.0-alpha.2`), không hồi quy so với alpha.1 |
| Build sản phẩm Windows + macOS `0.1.0-alpha.2` | ✅ | DMG universal, bộ cài NSIS + zip Windows, `.tpz` macOS + Windows; xem `docs/release_notes/Release_Notes_0.1.0-alpha.2.md` |
| Version `0.1.0-alpha.2`, tag `bamboo-v0.1.0-alpha.2` | ⚠️ | `version.py` đã nâng; tag chờ commit + CI xanh |

## Sprint 3 — `0.1.0-alpha.3`

| Task / DoD | Trạng thái | Bằng chứng |
| :--- | :---: | :--- |
| TL: audit patch + test, 100% tag | ✅ | `docs/rebase_reports/patch_audit_w5.md` (từ 27.8% lên 100%) |
| TL: `bamboo_modules/bamboo_core` link thành công | ✅ | Singleton `BambooCore` hoạt động |
| TL: diễn tập rebase + biên bản | ✅ | 659 commit upstream, 2 xung đột: `docs/rebase_reports/rebase_rehearsal_w5.md` |
| TL: diễn tập rebase lần 2 (kể cả phần chưa commit) + build + test | ✅ | 743 commit, 5 khối xung đột, 1445/1445 test pass: `docs/rebase_reports/rebase_rehearsal_20261014.md` |
| RT: Jolt mặc định + test C++ + fallback | ✅ | Đã có sẵn upstream cho project mới; thêm cảnh báo fallback; test C++ 3/3 + tích hợp 4/4 |
| BQ: 3 profile + `.gdbuild` + đo kích thước + test | ✅ | 2D **−30.0%** (thêm `optimize=size`, đạt ≥25%); Mobile −18.9% (dưới 20% của Sprint DoD); `docs/reports/binary_size_benchmark.md` |
| GAME: `game_dogfood/` + test gameplay + export desktop (macOS + Windows, alpha.3) | ✅ | Export macOS universal (46 MB, chạy được) + Windows `.exe`; gameplay 11/11; game là dự án mẫu, **không phải port từ Unity** |
| Build sản phẩm Windows + macOS `0.1.0-alpha.3` | ✅ | `docs/release_notes/Release_Notes_0.1.0-alpha.3.md` |
| Version `0.1.0-alpha.3`, tag `bamboo-v0.1.0-alpha.3` | ⚠️ | `version.py` đã nâng; tag chờ commit + CI xanh |

## Sprint 4 — `0.1.0-beta.1`

| Task / DoD | Trạng thái | Bằng chứng |
| :--- | :---: | :--- |
| GAME: crash reporter + test | ✅ | 8/8 |
| GAME: APK Android, chạy thiết bị thật 15 phút | ⛔ | Không có NDK 29 / Android templates / thiết bị |
| RT: script so sánh Unity vs Bamboo + test | ✅ | Từ chối xuất báo cáo từ dữ liệu mẫu |
| RT: báo cáo parity có số liệu thật | ⚠️ | Có số liệu phía Bamboo (dogfood: 60 FPS, khởi động ~0,5 s, 236 MiB RSS, 72 MiB Windows); thiếu đối chứng Unity |
| ALL: bug bash, triage, regression test | ✅ | Bug bash tự động 34 kiểm tra: 0 P0/P1/P2, 4 P3 (nghi upstream: VSync macOS, khựng shader lần đầu), 2 blocked (Linux/Android); `docs/reports/bug_bash_0.1.0-beta.1.md`; GUI/thiết bị thật vẫn cần người |
| TL: `check_release_branch.py` + test + chính sách | ✅ | `docs/policies/release_freeze_policy.md` |
| Version `0.1.0-beta.1` + build sản phẩm Windows/macOS | ✅ | `docs/release_notes/Release_Notes_0.1.0-beta.1.md` |
| GAME: PC ≥60 FPS, không rò rỉ bộ nhớ 15 phút | ✅ | soak 900 s: +0,051 MiB/phút; 60 FPS (VSync) |
| TL: cắt `release/0.1`, tag, branch protection | ⏸ | Cần commit công việc hiện tại trước (162+ file chưa commit) + quyền push |

## Sprint 5 — `0.1.0` (cập nhật 15/10/2026)

| Task / DoD | Trạng thái | Bằng chứng |
| :--- | :---: | :--- |
| ALL: rà soát P0/P1 | ⚠️ | GitHub Issues **đang tắt** → không xác minh được; `check_open_issues.py` giờ báo rõ thay vì "0" (BAMBOO-101). Bug bash: 0 P0/P1 |
| ALL: full regression + benchmark | ✅ | C++ 1436/1436, `[Regression]` pass; RAM 0% so với beta.1, FPS trong nhiễu (ngưỡng 1% < độ nhiễu đo) |
| BQ: `.dmg`, `.zip`, `.tpz`, `SHA256SUMS.txt` + test | ⚠️ | Đủ cho macOS/Windows (`bin/release/`, checksum OK); **chưa notarize** (thiếu Developer ID); Linux `.tar.xz` cần CI |
| TLS: `.pot` đồng bộ + test + Migration Guide | ✅ | 6 641 chuỗi, không đổi so với mã nguồn; hướng dẫn đủ 9 chương |
| TL: `0.1.0-rc.1` + CI | ⚠️ | rc.1 build và kiểm thử tại máy; CI của rc.1 chạy sau khi push |
| TL: Go/No-go | ✅ (họp) / ❌ (GO) | **NO-GO** 6/9: `docs/reports/go_nogo/go_nogo_0.1.0.md` |
| TL: `bamboo_prerelease = ""`, tag `bamboo-v0.1.0` | ⏸ | Không thực hiện vì NO-GO |

## Việc cần người/quyền bên ngoài để đóng các mục còn lại

1. Push nhánh lên GitHub để chạy CI 6 nền tảng (và cấp quyền tạo nhãn / branch protection).
2. Cài Android NDK `29.0.14206865` (+ thiết bị Android tầm trung) và Emscripten 6.0.1.
3. Apple Developer ID + tài khoản notarization; chứng chỉ code signing Windows.
4. Chọn game Unity nội bộ (đường dẫn dự án) để khảo sát, port và đo parity.
5. Quyết định về mục tiêu kích thước (xem `binary_size_benchmark.md`).
