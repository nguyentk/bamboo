# Bamboo build profiles

| Profile | SCons options file | Editor build profile | Purpose |
| :--- | :--- | :--- | :--- |
| 2D | `bamboo_2d.py` | `bamboo_2d.gdbuild` | 2D-only games: no 3D nodes, 3D physics, 3D navigation, XR |
| Mobile | `bamboo_mobile.py` | `bamboo_mobile.gdbuild` | Android/iOS: size-optimized, no XR/WebRTC/raycast |
| PC | `bamboo_pc.py` | `bamboo_pc.gdbuild` | Desktop reference build with every feature |

- `*.py` files are SCons option files: `scons ... profile=profiles/bamboo_2d.py`. Each sets an
  `extra_suffix` so the binaries do not overwrite the default build
  (e.g. `bin/bamboo.macos.template_release.arm64.2d`).
- `*.gdbuild` files are feature build profiles: `scons ... build_profile=profiles/bamboo_2d.gdbuild`,
  or open them in the editor (Project > Tools > Engine Compilation Configuration Editor) to also
  disable individual classes.
- Measured sizes: `docs/reports/binary_size_benchmark.md`
  (`python3 misc/scripts/measure_binary_sizes.py`).
