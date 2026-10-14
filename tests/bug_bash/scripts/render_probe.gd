# BAMBOO: Bug bash (RND) — load a scene with the current renderer and measure frame times.
# Run (windowed, needs a GPU): bamboo --path <project> --rendering-method <method> \
#     -s <abs path>/render_probe.gd -- --scene=res://scene.tscn [--frames=240]
# Prints `BUGBASH {json}` with the startup stutter (worst frame in the first 60 frames) and the steady state.
extends SceneTree

var scene_path := ""
var frames := 240
var times: Array[float] = []
var last_usec := 0


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--scene="):
			scene_path = arg.get_slice("=", 1)
		elif arg.begins_with("--frames="):
			frames = int(arg.get_slice("=", 1))
	var packed: PackedScene = load(scene_path)
	if packed == null:
		_finish(false, {"error": "cannot load scene"})
		return
	root.add_child(packed.instantiate())
	last_usec = Time.get_ticks_usec()


func _process(_delta: float) -> bool:
	var now := Time.get_ticks_usec()
	times.append((now - last_usec) / 1000.0)
	last_usec = now
	if times.size() < frames:
		return false
	var warmup := times.slice(1, 60)
	var steady := times.slice(60)
	steady.sort()
	var median: float = steady[steady.size() / 2]
	var p99: float = steady[int(steady.size() * 0.99)]
	var worst_warmup: float = warmup.max()
	_finish(true, {
		"renderer": RenderingServer.get_current_rendering_method(),
		"driver": RenderingServer.get_current_rendering_driver_name(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"worst_warmup_ms": snappedf(worst_warmup, 0.01),
		"steady_median_ms": snappedf(median, 0.01),
		"steady_p99_ms": snappedf(p99, 0.01),
		"steady_fps": snappedf(1000.0 / maxf(median, 0.001), 0.1),
		"vsync_mode": DisplayServer.window_get_vsync_mode(),
		"refresh_hz": snappedf(DisplayServer.screen_get_refresh_rate(DisplayServer.window_get_current_screen()), 0.1),
	})
	return true


func _finish(ok: bool, details: Dictionary) -> void:
	details["scene"] = scene_path
	print("BUGBASH ", JSON.stringify({"area": "rendering", "check": "render_probe", "passed": ok, "details": details}))
	quit(0 if ok else 1)
