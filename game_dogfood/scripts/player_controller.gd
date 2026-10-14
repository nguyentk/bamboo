# Player controller ported from the Unity CharacterController pattern:
# Update/FixedUpdate -> _physics_process, CharacterController.Move -> velocity + move_and_slide,
# Input.GetAxisRaw -> Input.get_vector on InputMap actions.
class_name PlayerController
extends CharacterBody3D

signal coin_collected(total: int)

@export var speed: float = 8.0
@export var jump_velocity: float = 4.5

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var coins := 0


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	if direction:
		velocity.x = direction.x * speed
		velocity.z = direction.z * speed
	else:
		velocity.x = move_toward(velocity.x, 0, speed)
		velocity.z = move_toward(velocity.z, 0, speed)

	move_and_slide()


func collect_coin() -> void:
	coins += 1
	coin_collected.emit(coins)
