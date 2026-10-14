# BAMBOO: Bug bash (RT) — Jolt physics stress and correctness checks.
# Run: bamboo --headless --path tests/bug_bash -s res://scripts/physics_stress.gd [-- --bodies=1000 --frames=600]
# Prints one `BUGBASH {json}` line per check and exits with 1 when a check fails.
extends SceneTree

var bodies := 1000
var frames := 600
var results: Array[Dictionary] = []
var world: Node3D


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--bodies="):
			bodies = int(arg.get_slice("=", 1))
		elif arg.begins_with("--frames="):
			frames = int(arg.get_slice("=", 1))
	world = Node3D.new()
	root.add_child(world)
	_run.call_deferred()


func _record(name: String, passed: bool, details: Dictionary) -> void:
	var entry := {"area": "physics", "check": name, "passed": passed, "details": details}
	results.append(entry)
	print("BUGBASH ", JSON.stringify(entry))


func _static_box(size: Vector3, pos: Vector3) -> StaticBody3D:
	var body := StaticBody3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	body.position = pos
	world.add_child(body)
	return body


func _rigid(shape_res: Shape3D, pos: Vector3) -> RigidBody3D:
	var body := RigidBody3D.new()
	var shape := CollisionShape3D.new()
	shape.shape = shape_res
	body.add_child(shape)
	body.position = pos
	world.add_child(body)
	return body


func _wait_physics(count: int) -> void:
	for i in count:
		await physics_frame


func _run() -> void:
	var server: String = ProjectSettings.get_setting("physics/3d/physics_engine")
	_record("physics_engine_is_jolt", server == "Jolt Physics", {"setting": server})

	# Large floor shared by every check.
	_static_box(Vector3(400, 1, 400), Vector3(0, -0.5, 0))

	# 1. Stack of N boxes falling and settling.
	var box := BoxShape3D.new()
	box.size = Vector3(0.5, 0.5, 0.5)
	var stack: Array[RigidBody3D] = []
	var side := ceili(pow(bodies, 1.0 / 3.0))
	for i in bodies:
		var x := i % side
		var y := (i / side) / side
		var z := (i / side) % side
		stack.append(_rigid(box, Vector3(x * 0.6 - side * 0.3, 1.0 + y * 0.6, z * 0.6 - side * 0.3)))

	var physics_ms: Array[float] = []
	var start := Time.get_ticks_usec()
	for i in frames:
		await physics_frame
		physics_ms.append(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0)
	var wall_s := (Time.get_ticks_usec() - start) / 1e6

	var fell_through := 0
	var invalid := 0
	var sleeping := 0
	for b in stack:
		var p := b.global_position
		if not (is_finite(p.x) and is_finite(p.y) and is_finite(p.z)):
			invalid += 1
		elif p.y < -1.0:
			fell_through += 1
		if b.sleeping:
			sleeping += 1
	physics_ms.sort()
	var avg := 0.0
	for v in physics_ms:
		avg += v
	avg /= maxf(1.0, physics_ms.size())
	var p95 := physics_ms[int(physics_ms.size() * 0.95)] if physics_ms.size() > 0 else 0.0
	_record("stack_no_tunneling_or_nan", fell_through == 0 and invalid == 0,
		{"bodies": bodies, "frames": frames, "fell_through": fell_through, "invalid": invalid})
	_record("stack_physics_time", p95 < 16.6,
		{"avg_ms": snappedf(avg, 0.01), "p95_ms": snappedf(p95, 0.01), "max_ms": snappedf(physics_ms[-1], 0.01),
		 "wall_time_s": snappedf(wall_s, 0.01), "sleeping": sleeping})

	# Free the stack so the remaining checks run on a quiet world.
	for b in stack:
		b.queue_free()
	await _wait_physics(2)

	# 2. Raycast must hit a thin wall from both sides.
	_static_box(Vector3(0.05, 4, 4), Vector3(50, 2, 0))
	await _wait_physics(2)
	var space := world.get_world_3d().direct_space_state
	var hits := []
	for dir in [1.0, -1.0]:
		var from := Vector3(50 - 5 * dir, 2, 0)
		var to := Vector3(50 + 5 * dir, 2, 0)
		var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(from, to))
		hits.append(snappedf(hit.position.x, 0.001) if hit else null)
	_record("raycast_hits_thin_wall_both_sides", hits[0] != null and hits[1] != null
		and absf(hits[0] - 49.975) < 0.01 and absf(hits[1] - 50.025) < 0.01, {"hit_x": hits})

	# 3. Fast body with continuous collision detection must not tunnel through a thin wall.
	var tunnel := {}
	for ccd in [true, false]:
		var z := 0.0 if ccd else 1.5
		var ball := SphereShape3D.new()
		ball.radius = 0.1
		var bullet := _rigid(ball, Vector3(40, 2, z))
		bullet.gravity_scale = 0.0
		bullet.continuous_cd = ccd
		bullet.linear_velocity = Vector3(300, 0, 0)
		await _wait_physics(60)
		tunnel["ccd" if ccd else "no_ccd"] = snappedf(bullet.global_position.x, 0.01)
		bullet.queue_free()
	_record("ccd_prevents_tunneling", tunnel["ccd"] < 50.0, {"final_x": tunnel,
		"note": "Without CCD tunneling at 300 m/s through a 5 cm wall is expected engine behavior."})

	# 4. Signals: Area3D.body_entered and RigidBody3D.body_entered (contact monitor).
	var area := Area3D.new()
	var area_shape := CollisionShape3D.new()
	var area_box := BoxShape3D.new()
	area_box.size = Vector3(2, 1, 2)
	area_shape.shape = area_box
	area.add_child(area_shape)
	area.position = Vector3(0, 3, 60)
	world.add_child(area)
	var area_hits := [0]
	area.body_entered.connect(func(_b): area_hits[0] += 1)
	var dropper := _rigid(box, Vector3(0, 6, 60))
	dropper.contact_monitor = true
	dropper.max_contacts_reported = 4
	var contacts := [0]
	dropper.body_entered.connect(func(_b): contacts[0] += 1)
	await _wait_physics(180)
	_record("area_body_entered_signal", area_hits[0] >= 1, {"count": area_hits[0]})
	_record("rigid_body_entered_signal", contacts[0] >= 1, {"count": contacts[0]})

	var failed := results.filter(func(r): return not r.passed).size()
	print("BUGBASH_SUMMARY physics %d/%d passed" % [results.size() - failed, results.size()])
	quit(1 if failed > 0 else 0)
