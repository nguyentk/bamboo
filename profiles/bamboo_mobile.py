# Bamboo Engine - Mobile optimized build profile.
# Usage: scons platform=android|ios target=template_release profile=profiles/bamboo_mobile.py
# Keeps 2D and 3D, drops desktop-oriented modules and optimizes for binary size (-Os).

extra_suffix = "mobile"

optimize = "size"

module_openxr_enabled = "no"
module_raycast_enabled = "no"
module_webrtc_enabled = "no"
