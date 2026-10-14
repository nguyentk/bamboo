# Bamboo modules

Bamboo-specific engine modules live here instead of in `modules/`, so that the Godot source tree
stays close to upstream and rebases stay cheap (see `docs/rebase_reports/`).

Build the engine with them:

```bash
scons platform=macos arch=arm64 target=editor custom_modules=bamboo_modules
```

| Module | Description |
| :--- | :--- |
| `bamboo_core` | `BambooCore` singleton: Bamboo product version information for scripts and tools. |

Conventions: classes registered in `ClassDB` use the `Bm`/`Bamboo` prefix; never rename or patch
Godot classes from here.
