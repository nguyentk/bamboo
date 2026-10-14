# Minimal assertion helpers for headless GDScript tests (run with `-s res://tests/<test>.gd`).
class_name BambooTestHelpers
extends RefCounted

var failures := 0
var checks := 0


func check(condition: bool, message: String) -> void:
	checks += 1
	if condition:
		print("  [PASS] ", message)
	else:
		failures += 1
		printerr("  [FAIL] ", message)


func check_near(value: float, expected: float, tolerance: float, message: String) -> void:
	check(absf(value - expected) <= tolerance, "%s (got %.3f, expected %.3f +/- %.3f)" % [message, value, expected, tolerance])


func summary(name: String) -> int:
	print("%s: %d/%d checks passed" % [name, checks - failures, checks])
	return 0 if failures == 0 else 1
