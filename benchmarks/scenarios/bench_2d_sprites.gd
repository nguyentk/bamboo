# 10,000 moving Sprite2D nodes (CanvasItem update + batching).
extends Node2D

const COUNT := 10000
var _sprites: Array[Sprite2D] = []
var _velocities: PackedVector2Array


func setup() -> void:
	var image := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	image.fill(Color(0.9, 0.6, 0.2))
	var texture := ImageTexture.create_from_image(image)
	var rng := RandomNumberGenerator.new()
	rng.seed = 1234
	_velocities.resize(COUNT)
	for i in COUNT:
		var sprite := Sprite2D.new()
		sprite.texture = texture
		sprite.position = Vector2(rng.randf_range(0, 1280), rng.randf_range(0, 720))
		_velocities[i] = Vector2(rng.randf_range(-100, 100), rng.randf_range(-100, 100))
		add_child(sprite)
		_sprites.append(sprite)


func _process(delta: float) -> void:
	for i in _sprites.size():
		var sprite := _sprites[i]
		var p := sprite.position + _velocities[i] * delta
		if p.x < 0.0 or p.x > 1280.0:
			_velocities[i].x = -_velocities[i].x
		if p.y < 0.0 or p.y > 720.0:
			_velocities[i].y = -_velocities[i].y
		sprite.position = p
