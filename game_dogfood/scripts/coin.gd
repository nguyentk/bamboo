# Collectible: Unity OnTriggerEnter(Collider) -> Area3D.body_entered.
extends Area3D

signal collected(by: Node3D)


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	rotate_y(delta * 2.0)


func _on_body_entered(body: Node3D) -> void:
	if body.has_method("collect_coin"):
		body.collect_coin()
		collected.emit(body)
		queue_free()
