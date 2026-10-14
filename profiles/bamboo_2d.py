# Bamboo Engine - 2D dedicated build profile.
# Usage: scons platform=<platform> target=template_release profile=profiles/bamboo_2d.py
# Removes 3D nodes, 3D physics/navigation and XR. Use for 2D-only games.

extra_suffix = "2d"

# -Os: needed to reach the >= 25% size target (-30% vs. the full template, macOS arm64; -17% without it).
# See docs/reports/binary_size_benchmark.md.
optimize = "size"

disable_3d = "yes"
disable_physics_3d = "yes"
disable_navigation_3d = "yes"
disable_xr = "yes"

module_csg_enabled = "no"
module_gridmap_enabled = "no"
module_jolt_physics_enabled = "no"
module_godot_physics_3d_enabled = "no"
module_openxr_enabled = "no"
module_glslang_enabled = "yes"
