# Memory footprint of a scene with 2,000 meshes, materials and collision shapes.
extends Node3D

const COUNT := 2000


func setup() -> void:
	for i in COUNT:
		var body := StaticBody3D.new()
		var instance := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		mesh.radial_segments = 16
		mesh.rings = 8
		instance.mesh = mesh
		var material := StandardMaterial3D.new()
		material.albedo_color = Color.from_hsv(float(i) / COUNT, 0.7, 0.9)
		instance.material_override = material
		var shape := CollisionShape3D.new()
		shape.shape = SphereShape3D.new()
		body.add_child(instance)
		body.add_child(shape)
		body.position = Vector3(i % 50, 0, i / 50)
		add_child(body)
