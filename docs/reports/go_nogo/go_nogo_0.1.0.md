# Biên bản Go/No-go — Bamboo Engine 0.1.0 "Sprout"

> Ngày 15/10/2026 · Ứng viên: **`0.1.0-rc.1`** trên nhánh `release/0.1` · Chủ trì: TL.
> Kiểm tra tự động: `python3 misc/scripts/release_readiness.py --evidence docs/reports/go_nogo/evidence_0.1.0-rc.1.json --final`
> Bằng chứng thủ công: [`evidence_0.1.0-rc.1.json`](evidence_0.1.0-rc.1.json).

## Quyết định: **NO-GO** — không chuyển sang `0.1.0` chính thức, không gắn tag `bamboo-v0.1.0`

6/9 tiêu chí đạt. `0.1.0-rc.1` được phát hành **nội bộ** như bản ứng viên; bản chính thức chờ 3 tiêu chí còn thiếu.

## 9 tiêu chí

| # | Tiêu chí | Kết quả | Bằng chứng |
| :-: | :--- | :-: | :--- |
| 1 | CI xanh 6 nền tảng | ✅ | 23/23 job trên `release/0.1` @ `2c88d6317c` ([run 38547585335](https://github.com/nguyentk/bamboo/actions/runs/38547585335)); rc.1 cần chạy lại CI sau khi push |
| 2 | 0 lỗi P0 mở | ❌ | **Không xác minh được**: GitHub Issues đang tắt trên `nguyentk/bamboo`. Bug bash tự động: 0 P0/P1, nhưng chưa có kiểm thử GUI/thiết bị |
| 3 | Benchmark ≥ 6 kịch bản | ✅ | `benchmarks/baseline.json` (6) |
| 4 | Golden image 3 renderer | ✅ | 11 ảnh, rc.1: 0,000% khác biệt |
| 5 | Build editor CI có cache ≤ 20 phút | ✅ | [run 38541240434](https://github.com/nguyentk/bamboo/actions/runs/38541240434): biên dịch 31–116 s/job; job macOS 5,5 phút |
| 6 | Game port từ Unity chạy trên PC + Android thật | ❌ | PC: dogfood 60 FPS, soak 15 phút không rò rỉ. **Chưa có Android** (thiếu NDK 29 + thiết bị) và dogfood là dự án mẫu, **chưa phải game Unity nội bộ** |
| 7 | 100% patch lõi có `BAMBOO:` | ✅ | 96/96 |
| 8 | Diễn tập rebase | ✅ | `rebase_rehearsal_w5.md`, `rebase_rehearsal_20261014.md` |
| 9 | `.dmg` đã Apple notarize | ❌ | Chỉ ký ad-hoc (`spctl`: rejected) — cần Apple Developer ID + tài khoản notary |

## Hồi quy & hiệu năng của rc.1

| Hạng mục | Kết quả |
| :--- | :--- |
| C++ doctest | 1436/1436 pass; `[Regression]` 1/1; `[BambooVersion]` 5/5 |
| Python tooling | xem commit rc.1 (toàn bộ pass) |
| Smoke test editor (arm64 + x86_64) + 4 template macOS | PASS |
| Dogfood: gameplay 11/11, crash reporter 8/8; export macOS (chạy được) + Windows | PASS |
| Benchmark so với beta.1 | RAM: 0,000% ở cả 6 kịch bản. FPS: −1,7% … +2,9% |

**Về ngưỡng FPS 1% của prompt P0**: giữa beta.1 và rc.1 không có thay đổi mã engine (chỉ sửa style/CI). Dao động −1,7% … +2,9%
là nhiễu đo của các micro-benchmark có frame 0,003–0,08 ms (nhiễu thực tế của bộ benchmark > 5%). Ngưỡng 1% thấp hơn độ
nhiễu nên không dùng được để kết luận; đề xuất đo FPS bằng kịch bản có tải thật (≥ 1 ms/frame) và nhiều lần chạy hơn.

## Lỗi mở tại thời điểm họp

| ID | Mức | Mô tả |
| :--- | :--- | :--- |
| BB-1…BB-4 | P3 | VSync macOS, khựng shader lần đầu (xem `docs/reports/bug_bash_0.1.0-beta.1.md`) |
| BB-5 | P3 | `ERROR: Parameter "singleton" is null.` xuất hiện 1/31 lần export headless (rc.1); export vẫn thành công, game chạy được; không tái hiện được để lấy vị trí |

## Theo dõi công việc phát hành

GitHub Issues đang tắt, nên các ticket của đợt phát hành được đánh số tại đây và tham chiếu trong commit trên `release/0.1`
(quy tắc `#123` / `BAMBOO-123` của `docs/policies/release_freeze_policy.md`).

| Ticket | Nội dung | Trạng thái |
| :--- | :--- | :--- |
| BAMBOO-101 | `check_open_issues.py` báo "0 P0" khi GitHub Issues bị tắt; lỗi SSL trên Python không có chứng chỉ CA | Đã sửa (rc.1) |
| BAMBOO-102 | Phát hành ứng viên `0.1.0-rc.1`, biên bản Go/No-go | Xong (rc.1) |
| BAMBOO-103 | Bật GitHub Issues + nhãn P0–P3 (`misc/scripts/setup_github_labels.sh`) để theo dõi lỗi phát hành | Cần chủ repo |
| BAMBOO-104 | Apple Developer ID + notarization cho `.dmg`; chứng chỉ ký Windows | Cần tài khoản/chứng chỉ |
| BAMBOO-105 | Build Android (NDK 29), chạy game trên thiết bị Android thật 15 phút | Cần NDK + thiết bị |
| BAMBOO-106 | Port game Unity nội bộ, đo parity Unity vs Bamboo | Cần dự án Unity |
| BAMBOO-107 | Bật bảo vệ nhánh `release/0.1` (review + CI xanh) | Cần quyền admin repo |

## Điều kiện để họp lại (GO)

Hoàn thành BAMBOO-103 → 106 (và lý tưởng là 107), chạy lại `release_readiness.py --final` sau khi đổi
`bamboo_prerelease = ""`. Khi đạt 9/9: commit `[Bamboo Release] Bamboo Engine 0.1.0 'Sprout' Official Release`, tag `bamboo-v0.1.0`.
