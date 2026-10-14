# Session telemetry and error log (autoload). Writes the last error report to user://crash_log.json.
extends Node

const LOG_PATH := "user://crash_log.json"


func _ready() -> void:
	print("[Telemetry] Initializing game session on Bamboo Engine: ", bamboo_version())
	print("[Telemetry] Device Model: ", OS.get_model_name(), " | OS: ", OS.get_name())


static func bamboo_version() -> String:
	return Engine.get_version_info().get("bamboo_string", "unknown")


func log_error(context: String, err_msg: String) -> Dictionary:
	var report := {
		"timestamp": Time.get_datetime_string_from_system(true),
		"bamboo_version": bamboo_version(),
		"godot_version": Engine.get_version_info().get("string", ""),
		"os": OS.get_name(),
		"device_model": OS.get_model_name(),
		"context": context,
		"error": err_msg,
	}
	var file := FileAccess.open(LOG_PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report))
		file.close()
	else:
		push_error("CrashReporter: cannot write %s" % LOG_PATH)
	return report
