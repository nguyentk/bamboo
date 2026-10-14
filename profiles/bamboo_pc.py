# Bamboo Engine - PC (desktop) build profile with the full feature set.
# Usage: scons platform=windows|linuxbsd|macos target=template_release profile=profiles/bamboo_pc.py
# Nothing is stripped; this profile documents the reference build used for size comparisons.

extra_suffix = "pc"

optimize = "speed"
