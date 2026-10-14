# Bamboo regression tests

Every P0/P1 fix must come with a test that fails before the fix and passes after it.

- C++ (doctest): `tests/regression/test_regression_<id>.cpp`, test cases tagged `[Regression]`.
  Files under `tests/` are compiled automatically with `tests=yes` (see `tests/SCsub`).
  Run: `bin/bamboo.<platform>.editor.<arch> --test --test-case="*[Regression]*"`.
- Build tooling (Python): `tests/python_build/test_regression_<id>.py`.

`<id>` is the GitHub issue number, or a `BAMBOO-REG-<n>` identifier for problems found before the
issue tracker existed.

| ID | Problem | Test |
| :--- | :--- | :--- |
| BAMBOO-REG-1 | A `# BAMBOO:` comment inserted into the `version_info_builder` template produced an invalid preprocessor line in `core/version_generated.gen.h` and broke the iOS simulator build. | `tests/python_build/test_regression_version_header.py`, `tests/regression/test_regression_version_header.cpp` |
| BAMBOO-REG-2 | A project requesting an unavailable 3D physics engine silently fell back to another engine. | `tests/python_build/test_jolt_physics_integration.py` (`test_unknown_engine_falls_back_with_warning`) |
