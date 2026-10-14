# Crash reporter tests. Run: bamboo --headless --path game_dogfood -s res://tests/test_crash_reporter.gd
extends SceneTree

const CrashReporterScript := preload("res://scripts/crash_reporter.gd")
const Helpers := preload("res://tests/test_helpers.gd")

var t = Helpers.new()


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var reporter: Node = CrashReporterScript.new()
	root.add_child(reporter)
	var expected_version: String = Engine.get_version_info().get("bamboo_string", "")
	t.check(not expected_version.is_empty(), "engine reports a Bamboo version")

	if FileAccess.file_exists(CrashReporterScript.LOG_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(CrashReporterScript.LOG_PATH))
	var report: Dictionary = reporter.log_error("test_context", "Simulated failure 42")

	t.check(FileAccess.file_exists(CrashReporterScript.LOG_PATH), "crash log written to user://crash_log.json")
	var data = JSON.parse_string(FileAccess.get_file_as_string(CrashReporterScript.LOG_PATH))
	t.check(data is Dictionary, "crash log is valid JSON")
	if data is Dictionary:
		t.check(data.get("bamboo_version") == expected_version, "bamboo_version = %s" % expected_version)
		t.check(data.get("error") == "Simulated failure 42", "error message stored")
		t.check(data.get("context") == "test_context", "context stored")
		t.check(not String(data.get("timestamp", "")).is_empty(), "timestamp stored")
	t.check(report.get("bamboo_version") == expected_version, "log_error returns the report")

	DirAccess.remove_absolute(ProjectSettings.globalize_path(CrashReporterScript.LOG_PATH))
	reporter.queue_free()
	await process_frame
	quit(t.summary("test_crash_reporter"))
