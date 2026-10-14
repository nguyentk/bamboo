# Bamboo benchmark runner: runs every scenario, samples frame/physics/memory metrics and writes JSON.
# Usage: bamboo --headless --path benchmarks -- --output=/abs/path/results.json [--only=name1,name2]
extends Node

const SCENARIOS := [
	"bench_2d_sprites",
	"bench_3d_draw_calls",
	"bench_physics_3d_stack",
	"bench_gdscript_cpu",
	"bench_startup_time",
	"bench_memory_footprint",
]
const WARMUP_FRAMES := 30
const MEASURE_FRAMES := 240

var _startup_ms := 0


func _ready() -> void:
	# Time from engine start to the main scene being ready.
	_startup_ms = Time.get_ticks_msec()
	var args := _parse_user_args()
	var output: String = args.get("output", "user://results.json")
	var only: Array = String(args.get("only", "")).split(",", false)

	var results: Array[Dictionary] = []
	for scenario_name in SCENARIOS:
		if not only.is_empty() and not only.has(scenario_name):
			continue
		print("[Bench] Running ", scenario_name)
		var result: Dictionary = await _run_scenario(scenario_name)
		result["name"] = scenario_name
		results.append(result)

	var version := Engine.get_version_info()
	var report := {
		"schema_version": 1,
		"bamboo_version": version.get("bamboo_string", ""),
		"godot_version": "%d.%d.%d-%s" % [version["major"], version["minor"], version["patch"], version["status"]],
		"build": version["build"],
		"renderer": RenderingServer.get_current_rendering_method(),
		"headless": DisplayServer.get_name() == "headless",
		"physics_engine": ProjectSettings.get_setting("physics/3d/physics_engine"),
		"os": OS.get_name(),
		"cpu": OS.get_processor_name(),
		"benchmarks": results,
	}
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file == null:
		push_error("Cannot write benchmark results to %s" % output)
		get_tree().quit(1)
		return
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("[Bench] Results written to ", output)
	get_tree().quit(0)


func _parse_user_args() -> Dictionary:
	var args := {}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--") and arg.contains("="):
			var parts := arg.substr(2).split("=", true, 1)
			args[parts[0]] = parts[1]
	return args


func _run_scenario(scenario_name: String) -> Dictionary:
	var scenario: Node = load("res://scenarios/%s.gd" % scenario_name).new()
	var memory_before := OS.get_static_memory_usage()
	add_child(scenario)
	if scenario.has_method("setup"):
		await scenario.setup()

	var result := {}
	if scenario.has_method("run_workload"):
		# CPU-bound scenarios measure their own workload.
		result = await scenario.run_workload()
	else:
		result = await _sample_frames(scenario)

	if scenario_name == "bench_startup_time":
		result["startup_ms"] = float(_startup_ms)
	result["memory_bytes"] = OS.get_static_memory_usage()
	result["memory_delta_bytes"] = OS.get_static_memory_usage() - memory_before

	scenario.queue_free()
	await get_tree().process_frame
	return result


func _sample_frames(scenario: Node) -> Dictionary:
	for i in WARMUP_FRAMES:
		await get_tree().process_frame

	# Physics scenarios are sampled per physics step: in uncapped headless runs most idle frames
	# would not contain any physics step at all.
	var per_physics_step: bool = scenario.get("sample_physics_steps") == true
	var frame_times: Array[float] = []
	var physics_times: Array[float] = []
	var last := Time.get_ticks_usec()
	for i in MEASURE_FRAMES:
		if per_physics_step:
			await get_tree().physics_frame
		else:
			await get_tree().process_frame
		var now := Time.get_ticks_usec()
		frame_times.append((now - last) / 1000.0)
		last = now
		physics_times.append(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0)

	var avg := _average(frame_times)
	return {
		"fps_avg": 1000.0 / avg if avg > 0.0 else 0.0,
		"frame_time_ms": avg,
		"frame_time_p95_ms": _percentile(frame_times, 0.95),
		# Only meaningful when sampling per physics step; the raw monitor value is kept for reference.
		"physics_time_ms": _average(physics_times) if per_physics_step else 0.0,
		"physics_monitor_ms": _average(physics_times),
		"node_count": Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
	}


static func _average(values: Array[float]) -> float:
	if values.is_empty():
		return 0.0
	var total := 0.0
	for v in values:
		total += v
	return total / values.size()


static func _percentile(values: Array[float], p: float) -> float:
	if values.is_empty():
		return 0.0
	var sorted := values.duplicate()
	sorted.sort()
	return sorted[clampi(int(ceil(p * sorted.size())) - 1, 0, sorted.size() - 1)]
