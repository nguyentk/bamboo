# 500 RigidBody3D boxes (10x10 base, 5 levels) collapsing on a static floor.
extends Node3D

const SIDE := 10
const LEVELS := 5

## Tells the runner to sample once per physics step.
var sample_physics_steps := true


func setup() -> void:
	var floor_body := StaticBody3D.new()
	var floor_shape := CollisionShape3D.new()
	var floor_box := BoxShape3D.new()
	floor_box.size = Vector3(100, 1, 100)
	floor_shape.shape = floor_box
	floor_body.add_child(floor_shape)
	floor_body.position = Vector3(0, -0.5, 0)
	add_child(floor_body)

	var box := BoxShape3D.new()
	box.size = Vector3.ONE
	for level in LEVELS:
		for x in SIDE:
			for z in SIDE:
				var body := RigidBody3D.new()
				var shape := CollisionShape3D.new()
				shape.shape = box
				body.add_child(shape)
				# Slight offsets per level make the tower unstable so it collapses.
				body.position = Vector3(x * 1.05 - SIDE / 2.0 + level * 0.3, 0.5 + level * 1.05, z * 1.05 - SIDE / 2.0)
				add_child(body)
