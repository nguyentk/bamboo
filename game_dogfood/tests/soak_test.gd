# BAMBOO: Dogfood soak test (sprint 0.1.0-beta.1, GAME/ALL bug bash).
# Plays the main level with an autopilot (steers the player to the nearest coin through the InputMap, jumps
# now and then, respawns coins) and samples FPS, memory and object counts once per second.
# Run: bamboo --path game_dogfood -s res://tests/soak_test.gd [--headless] -- --seconds=900 [--out=/abs/result.json]
# Prints `BUGBASH {json}` lines; exits with 1 when the player leaves the level, a script error stops the game or
# memory keeps growing (> 1 MiB/min after warm-up).
extends SceneTree

const COIN_SCENE := "res://scenes/coin.tscn"
const LEAK_MIB_PER_MIN := 1.0
const WARMUP_S := 30.0

var seconds := 900.0
var out_path := ""
var level: Node3D
var player: CharacterBody3D
var coins_root: Node3D
var coin_scene: PackedScene
var rng := RandomNumberGenerator.new()
var elapsed := 0.0
var next_sample := 1.0
var next_spawn := 0.0
var samples: Array[Dictionary] = []
var frames_since_sample := 0
var min_y := INF
var collected := 0
var spawned := 0


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--seconds="):
			seconds = float(arg.get_slice("=", 1))
		elif arg.begins_with("--out="):
			out_path = arg.get_slice("=", 1)
	rng.seed = 2026
	coin_scene = load(COIN_SCENE)
	level = (load("res://scenes/main_level.tscn") as PackedScene).instantiate()
	root.add_child(level)
	player = level.get_node("Player")
	coins_root = level.get_node("Coins")
	player.coin_collected.connect(func(total: int): collected = total)


func _process(delta: float) -> bool:
	elapsed += delta
	frames_since_sample += 1
	_drive()
	if elapsed >= next_spawn:
		next_spawn = elapsed + 5.0
		_respawn_coins()
	min_y = minf(min_y, player.global_position.y)
	if elapsed >= next_sample:
		_sample()
		next_sample += 1.0
	if elapsed >= seconds or player.global_position.y < -10.0:
		_finish()
		return true
	return false


func _drive() -> void:
	var target: Node3D = null
	var best := INF
	for coin in coins_root.get_children():
		var d := (coin as Node3D).global_position.distance_to(player.global_position)
		if d < best:
			best = d
			target = coin
	for action in ["move_left", "move_right", "move_forward", "move_back"]:
		Input.action_release(action)
	if target:
		var local := player.global_transform.basis.inverse() * (target.global_position - player.global_position)
		var dir := Vector2(local.x, local.z).normalized()
		if dir.x > 0.0:
			Input.action_press("move_right", dir.x)
		elif dir.x < 0.0:
			Input.action_press("move_left", -dir.x)
		if dir.y > 0.0:
			Input.action_press("move_back", dir.y)
		elif dir.y < 0.0:
			Input.action_press("move_forward", -dir.y)
	if rng.randf() < 0.01:
		Input.action_press("jump")
	else:
		Input.action_release("jump")


func _respawn_coins() -> void:
	while coins_root.get_child_count() < 3:
		var coin: Node3D = coin_scene.instantiate()
		coin.position = Vector3(rng.randf_range(-8.0, 8.0), 1.0, rng.randf_range(-8.0, 8.0))
		coins_root.add_child(coin)
		spawned += 1


func _sample() -> void:
	samples.append({
		"t": snappedf(elapsed, 0.1),
		"fps": Performance.get_monitor(Performance.TIME_FPS),
		"frames": frames_since_sample,
		"static_mib": Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0,
		"objects": Performance.get_monitor(Performance.OBJECT_COUNT),
		"nodes": Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		"resources": Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT),
	})
	frames_since_sample = 0


# Least-squares slope of `key` per minute over the samples after the warm-up.
func _slope_per_min(key: String) -> float:
	var pts := samples.filter(func(s): return s.t >= WARMUP_S)
	if pts.size() < 10:
		return 0.0
	var n := float(pts.size())
	var sx := 0.0
	var sy := 0.0
	var sxx := 0.0
	var sxy := 0.0
	for s in pts:
		sx += s.t
		sy += s[key]
		sxx += s.t * s.t
		sxy += s.t * s[key]
	var denom := n * sxx - sx * sx
	return 0.0 if denom == 0.0 else (n * sxy - sx * sy) / denom * 60.0


func _finish() -> void:
	var fps_values: Array = samples.slice(2).map(func(s): return float(s.frames))
	fps_values.sort()
	var headless := DisplayServer.get_name() == "headless"
	var mem_slope := _slope_per_min("static_mib")
	var details := {
		"seconds": snappedf(elapsed, 0.1),
		"headless": headless,
		"renderer": RenderingServer.get_current_rendering_method(),
		"fps_median": fps_values[fps_values.size() / 2] if fps_values.size() > 0 else 0,
		"fps_min": fps_values[0] if fps_values.size() > 0 else 0,
		"fps_p1": fps_values[int(fps_values.size() * 0.01)] if fps_values.size() > 0 else 0,
		"static_mib_start": snappedf(samples[0].static_mib, 0.01) if samples.size() > 0 else 0,
		"static_mib_end": snappedf(samples[-1].static_mib, 0.01) if samples.size() > 0 else 0,
		"static_mib_per_min": snappedf(mem_slope, 0.001),
		"objects_per_min": snappedf(_slope_per_min("objects"), 0.01),
		"nodes_end": samples[-1].nodes if samples.size() > 0 else 0,
		"coins_spawned": spawned,
		"coins_collected": collected,
		"player_min_y": snappedf(min_y, 0.01),
	}
	var in_level := min_y > -10.0
	var no_leak := mem_slope < LEAK_MIB_PER_MIN
	var finished := elapsed >= seconds
	var entry := {"area": "game", "check": "dogfood_soak", "passed": in_level and no_leak and finished, "details": details}
	print("BUGBASH ", JSON.stringify(entry))
	if not out_path.is_empty():
		var f := FileAccess.open(out_path, FileAccess.WRITE)
		if f:
			f.store_string(JSON.stringify({"summary": entry, "samples": samples}, "  "))
	quit(0 if entry.passed else 1)
