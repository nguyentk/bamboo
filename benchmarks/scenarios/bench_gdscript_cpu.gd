# CPU-bound GDScript workloads: recursion, Vector3/Transform3D math, sorting.
extends Node

const RUNS := 5


func run_workload() -> Dictionary:
	var fib_ms := _measure(func(): _fib(24))
	var vector_ms := _measure(_vector_math)
	var sort_ms := _measure(_sort_array)
	var total := fib_ms + vector_ms + sort_ms
	return {
		"frame_time_ms": total,
		"fps_avg": 1000.0 / total if total > 0.0 else 0.0,
		"physics_time_ms": 0.0,  # No physics in this scenario.
		"fib_ms": fib_ms,
		"vector_math_ms": vector_ms,
		"sort_ms": sort_ms,
	}


func _measure(workload: Callable) -> float:
	var best := INF
	for i in RUNS:
		var start := Time.get_ticks_usec()
		workload.call()
		best = minf(best, (Time.get_ticks_usec() - start) / 1000.0)
	return best


func _fib(n: int) -> int:
	return n if n < 2 else _fib(n - 1) + _fib(n - 2)


func _vector_math() -> void:
	var t := Transform3D(Basis.from_euler(Vector3(0.1, 0.2, 0.3)), Vector3(1, 2, 3))
	var v := Vector3(1, 0, 0)
	for i in 200000:
		v = t * v
		v = v.normalized()


func _sort_array() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	var values: Array[int] = []
	values.resize(100000)
	for i in values.size():
		values[i] = rng.randi()
	values.sort()
