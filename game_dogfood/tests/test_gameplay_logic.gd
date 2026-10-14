# Gameplay logic tests for the dogfood game.
# Run: bamboo --headless --path game_dogfood -s res://tests/test_gameplay_logic.gd
extends SceneTree

const PlayerScene := preload("res://scenes/player.tscn")
const CoinScene := preload("res://scenes/coin.tscn")
const Helpers := preload("res://tests/test_helpers.gd")

var t = Helpers.new()


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	print("Physics engine: ", ProjectSettings.get_setting("physics/3d/physics_engine"))
	await _test_falls_under_gravity()
	await _test_moves_with_input()
	await _test_collects_coin()
	quit(t.summary("test_gameplay_logic"))


func _make_floor(parent: Node) -> void:
	var floor_body := StaticBody3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(50, 1, 50)
	shape.shape = box
	floor_body.add_child(shape)
	floor_body.position = Vector3(0, -0.5, 0)
	parent.add_child(floor_body)


func _physics_frames(count: int) -> void:
	for i in count:
		await physics_frame


func _test_falls_under_gravity() -> void:
	print("Gravity:")
	var world := Node3D.new()
	root.add_child(world)
	var player: CharacterBody3D = PlayerScene.instantiate()
	player.position = Vector3(0, 50, 0)
	world.add_child(player)

	var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
	var steps := 30
	await _physics_frames(steps)
	var elapsed := steps / float(Engine.physics_ticks_per_second)
	t.check(player.velocity.y < 0.0, "velocity.y becomes negative while airborne")
	t.check_near(player.velocity.y, -gravity * elapsed, gravity * 2.0 / Engine.physics_ticks_per_second, "velocity.y follows -g * t")
	t.check(player.position.y < 50.0, "player falls")
	world.queue_free()
	await process_frame


func _test_moves_with_input() -> void:
	print("Movement:")
	var world := Node3D.new()
	root.add_child(world)
	_make_floor(world)
	var player: CharacterBody3D = PlayerScene.instantiate()
	player.position = Vector3(0, 0.1, 0)
	world.add_child(player)
	await _physics_frames(10)
	t.check(player.is_on_floor(), "player lands on the floor")

	var start_x: float = player.position.x
	Input.action_press("move_right")
	await _physics_frames(30)
	t.check_near(player.velocity.x, player.speed, 0.01, "velocity.x reaches speed while move_right is held")
	t.check(player.position.x > start_x + 2.0, "player moves to the right")
	Input.action_release("move_right")
	await _physics_frames(5)
	t.check_near(player.velocity.x, 0.0, 0.01, "player stops when the input is released")

	# `Input.action_press()` marks the action as just pressed for the *next* physics step
	# (pressed_physics_frame = physics_frames + 1), and `await physics_frame` resumes at the start of
	# a step, before nodes run `_physics_process()`. Wait two steps so the jump has been processed.
	Input.action_press("jump")
	await physics_frame
	await physics_frame
	Input.action_release("jump")
	t.check(player.velocity.y > 0.0, "jump gives an upward velocity")
	world.queue_free()
	await process_frame


func _test_collects_coin() -> void:
	print("Coin pickup (Area3D.body_entered):")
	var world := Node3D.new()
	root.add_child(world)
	_make_floor(world)
	var player: CharacterBody3D = PlayerScene.instantiate()
	player.position = Vector3(0, 0.1, 0)
	world.add_child(player)
	var coin: Area3D = CoinScene.instantiate()
	coin.position = Vector3(3, 1, 0)
	world.add_child(coin)

	var events := []
	coin.collected.connect(func(by: Node3D) -> void: events.append(by))
	await _physics_frames(10)
	Input.action_press("move_right")
	await _physics_frames(60)
	Input.action_release("move_right")
	t.check(events.size() == 1, "collected signal emitted once")
	t.check(events.size() == 1 and events[0] == player, "collected by the player")
	t.check(player.coins == 1, "player coin counter incremented")
	world.queue_free()
	await process_frame
