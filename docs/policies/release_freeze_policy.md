# Bamboo Engine — Chính sách Feature Freeze & Nhánh phát hành

> Áp dụng từ `0.1.0-beta.1` (W8). Công cụ kiểm tra: [`misc/scripts/check_release_branch.py`](../../misc/scripts/check_release_branch.py) · test: [`tests/python_build/test_release_freeze.py`](../../tests/python_build/test_release_freeze.py)

## 1. Nhánh

| Nhánh | Nhận gì | Ghi chú |
| :--- | :--- | :--- |
| `bamboo/main` | Tính năng + sửa lỗi | Nhánh phát triển chính |
| `release/<major>.<minor>` (vd. `release/0.1`) | **Chỉ sửa lỗi** | Cắt từ `bamboo/main` tại feature freeze |
| `upstream/master` | — | Mirror Godot, không commit (push đã bị chặn: `git remote set-url --push upstream DISABLE`) |

## 2. Thủ tục feature freeze (TL)

1. Đảm bảo `bamboo/main` xanh CI và `python3 misc/scripts/audit_bamboo_patches.py` báo 100% patch có tag.
2. Cắt nhánh và đổi phiên bản:

```bash
git checkout -b release/0.1 bamboo/main
```

   Trong `version.py`: `bamboo_prerelease = "beta.1"`. Commit: `[Bamboo Release] Bump version to 0.1.0-beta.1 and establish release/0.1 branch`.
3. Kiểm tra:

```bash
python3 misc/scripts/check_release_branch.py --branch release/0.1
```

4. Gắn tag `bamboo-v0.1.0-beta.1` sau khi CI xanh; push nhánh và tag.
5. Bật branch protection trên GitHub cho `release/*`: bắt buộc PR, ≥ 1 review của TL, toàn bộ CI (desktop, mobile, web) xanh, không force-push.

## 3. Quy tắc trên nhánh release

- **Chỉ nhận sửa lỗi** (`fix:`, `[Bamboo Fix]`). Commit `feat:` / `feature:` / `[Bamboo Feature]` bị `check_release_branch.py` từ chối.
- Không đổi API công khai (`ClassDB`, GDExtension), không refactor lớn, không cập nhật thư viện `thirdparty/` trừ bản vá bảo mật.
- Mỗi commit tham chiếu một ticket (`#123` hoặc `BAMBOO-123`) — kiểm tra bằng `check_open_issues.commits_without_ticket`.
- Mọi bản sửa P0/P1 kèm test hồi quy (`tests/regression/`, xem README trong thư mục đó).
- `bamboo_prerelease` chỉ được là `beta.N`, `rc.N` hoặc `""` (bản chính thức).

## 4. Cherry-pick

1. Sửa lỗi **trên `release/0.1` trước** (PR vào nhánh release).
2. Sau khi merge, cherry-pick sang `bamboo/main`:

```bash
git checkout bamboo/main
```

```bash
git cherry-pick -x <commit>
```

   `-x` ghi lại commit gốc để truy vết. Nếu xung đột, mở PR riêng vào `bamboo/main` và liên kết với PR gốc.
3. Không cherry-pick theo chiều ngược lại (`bamboo/main` → `release/*`) trừ khi TL duyệt.

## 5. Tiến trình phiên bản

`beta.1` (freeze) → `beta.N` (sửa lỗi) → `rc.1` (ứng viên, chạy lại toàn bộ test/benchmark/golden image) → `""` (bản chính thức, tag `bamboo-v0.1.0`) → `0.1.1`, `0.1.2` (hotfix trên cùng nhánh).

## 6. Điều kiện GO phát hành

Được kiểm bằng `python3 misc/scripts/release_readiness.py` (9 tiêu chí của Go/No-go, xem `docs/release_notes/`).
