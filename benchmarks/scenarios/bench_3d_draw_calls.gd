# 2,500 MeshInstance3D boxes (50x50 grid) with dynamic lights.
extends Node3D

const GRID := 50


func setup() -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3(0.8, 0.8, 0.8)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.3, 0.6, 0.9)
	for x in GRID:
		for z in GRID:
			var instance := MeshInstance3D.new()
			instance.mesh = mesh
			instance.material_override = material
			instance.position = Vector3(x - GRID / 2.0, 0.0, z - GRID / 2.0)
			add_child(instance)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 30, 0)
	add_child(sun)
	for i in 4:
		var lamp := OmniLight3D.new()
		lamp.position = Vector3(-15 + i * 10, 3, 0)
		lamp.omni_range = 12.0
		add_child(lamp)

	var camera := Camera3D.new()
	camera.position = Vector3(0, 30, 40)
	add_child(camera)
	camera.look_at(Vector3.ZERO)
	camera.make_current()


func _process(delta: float) -> void:
	rotate_y(delta * 0.2)
