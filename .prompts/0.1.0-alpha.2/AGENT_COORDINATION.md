# 🎋 Sprint Coordination: Bamboo 0.1.0-alpha.2 (W3 – W4)

> **Mục tiêu Sprint**: Mở rộng CI sang Mobile & Web, hiện thực bộ đo Benchmark tự động, thiết lập Golden-Image test, và xây dựng công cụ chuyển đổi tài nguyên Unity3D.  
> **Thời gian**: 26/10/2026 – 06/11/2026  
> **Mốc phát hành**: **`Bamboo 0.1.0-alpha.2`** (Cuối W4 - 06/11/2026)

---

## 1. Phân công Vai trò & Nhiệm vụ

| Agent | File Prompt | Trách nhiệm chính |
| :---: | :--- | :--- |
| **PLT** | `PROMPT_PLT_MOBILE_WEB_CI.md` | CI Android (APK/AAB), iOS, Web (threaded & no-thread), cấu hình ký số. |
| **RT / RND** | `PROMPT_RT_RND_BENCHMARK_SUITE.md` | Dựng dự án `bamboo-benchmarks` chạy `--headless`, xuất JSON, thiết lập nightly CI job. |
| **RND** | `PROMPT_RND_GOLDEN_IMAGE_TESTS.md` | Dựng Golden-image test cho 3 renderer (Forward+, Mobile, Compatibility) trên Linux/Mac. |
| **GAME** | `PROMPT_GAME_UNITY_ASSET_CONVERTER.md` | Xây dựng công cụ chuyển đổi asset Unity (Models, Textures, Materials, Prefabs sang `.tscn`). |

---

## 2. Luồng Phối hợp (Handoff Workflow)

```
       ┌────────────────────────────────────────────────────────┐
       │             Kế thừa từ 0.1.0-alpha.1                   │
       └──────────────────────────┬─────────────────────────────┘
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    ▼                             ▼                             ▼
[PLT: CI Mobile & Web]   [RT/RND: Benchmark Suite]     [GAME: Asset Converter]
    │                             │                             │
    │                    [RND: Golden-Image]                    │
    └─────────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
                     [TAG: bamboo-v0.1.0-alpha.2]
```

1. **PLT Agent**: Hoàn thiện matrix CI đầy đủ cho Android, iOS, Web trên `.github/workflows/`.
2. **RT & RND Agent**: Dựng khung đo lường benchmark tự động xuất JSON (sprites 2D, draw-calls 3D, physics stress, startup time). RND thiết lập so sánh hình ảnh render mẫu (Golden image).
3. **GAME Agent**: Xây dựng tool chuyển đổi asset 3D và prefab từ dự án Unity sang Bamboo, có unit test kiểm chứng độ lệch vị trí và mapping material.
4. **Hợp nhất**: Chạy nightly test đầu tiên, gắn tag release `bamboo-v0.1.0-alpha.2`.

---

## 3. Tiêu chí Hoàn thành Sprint (Sprint DoD)
* [ ] Matrix CI đạt 6/6 nền tảng xanh (Windows, macOS, Linux, Android, iOS, Web).
* [ ] Benchmark suite chạy thành công không crash ở chế độ `--headless` và xuất JSON chuẩn.
* [ ] Golden-image test chạy tự động trên Linux (llvmpipe) và macOS (Metal) với ngưỡng sai số kiểm soát.
* [ ] Bộ asset 3D cốt lõi của game Unity nội bộ chuyển đổi thành công sang định dạng Bamboo.
* [ ] Gắn tag git `bamboo-v0.1.0-alpha.2`.
