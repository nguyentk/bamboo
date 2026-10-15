/**************************************************************************/
/*  test_bamboo_version.cpp                                               */
/**************************************************************************/
/*                         This file is part of:                          */
/*                             GODOT ENGINE                               */
/*                        https://godotengine.org                         */
/**************************************************************************/
/* Copyright (c) 2014-present Godot Engine contributors (see AUTHORS.md). */
/* Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.                  */
/*                                                                        */
/* Permission is hereby granted, free of charge, to any person obtaining  */
/* a copy of this software and associated documentation files (the        */
/* "Software"), to deal in the Software without restriction, including    */
/* without limitation the rights to use, copy, modify, merge, publish,    */
/* distribute, sublicense, and/or sell copies of the Software, and to     */
/* permit persons to whom the Software is furnished to do so, subject to  */
/* the following conditions:                                              */
/*                                                                        */
/* The above copyright notice and this permission notice shall be         */
/* included in all copies or substantial portions of the Software.        */
/*                                                                        */
/* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,        */
/* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF     */
/* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. */
/* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY   */
/* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,   */
/* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE      */
/* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                 */
/**************************************************************************/

// BAMBOO: Tests for the Bamboo product version (dual versioning with the Godot base version).

#include "tests/test_macros.h"

TEST_FORCE_LINK(test_bamboo_version)

#include "core/config/engine.h"
#include "core/version.h"

namespace TestBambooVersion {

TEST_CASE("[BambooVersion] Bamboo version fields in Engine singleton") {
	const Dictionary version_info = Engine::get_singleton()->get_version_info();

	CHECK(version_info.has("bamboo_major"));
	CHECK(version_info.has("bamboo_minor"));
	CHECK(version_info.has("bamboo_patch"));
	CHECK(version_info.has("bamboo_prerelease"));
	CHECK(version_info.has("bamboo_codename"));
	CHECK(version_info.has("bamboo_string"));

	CHECK_EQ(int(version_info["bamboo_major"]), BAMBOO_VERSION_MAJOR);
	CHECK_EQ(int(version_info["bamboo_minor"]), BAMBOO_VERSION_MINOR);
	CHECK_EQ(int(version_info["bamboo_patch"]), BAMBOO_VERSION_PATCH);
	CHECK_EQ(String(version_info["bamboo_prerelease"]), String(BAMBOO_VERSION_PRERELEASE));
	CHECK_EQ(String(version_info["bamboo_codename"]), String(BAMBOO_VERSION_CODENAME));
	CHECK_EQ(String(version_info["bamboo_string"]), String(BAMBOO_VERSION_STRING));
}

TEST_CASE("[BambooVersion] Godot base version is preserved for GDExtension compatibility") {
	const Dictionary version_info = Engine::get_singleton()->get_version_info();

	// GDExtension `compatibility_minimum` checks compare against these values.
	CHECK_EQ(int(version_info["major"]), 4);
	CHECK_EQ(int(version_info["minor"]), 8);
	CHECK_EQ(int(version_info["major"]), GODOT_VERSION_MAJOR);
	CHECK_EQ(int(version_info["minor"]), GODOT_VERSION_MINOR);
	CHECK_EQ(int(version_info["patch"]), GODOT_VERSION_PATCH);
}

TEST_CASE("[BambooVersion] Version string is consistent with its components") {
	String expected = itos(BAMBOO_VERSION_MAJOR) + "." + itos(BAMBOO_VERSION_MINOR) + "." + itos(BAMBOO_VERSION_PATCH);
	const String prerelease = BAMBOO_VERSION_PRERELEASE;
	if (!prerelease.is_empty()) {
		expected += "-" + prerelease;
	}
	CHECK_EQ(String(BAMBOO_VERSION_STRING), expected);
	CHECK_FALSE(String(BAMBOO_VERSION_CODENAME).is_empty());
}

TEST_CASE("[BambooVersion] Display strings contain the Bamboo and Godot base versions") {
	const String full_build = BAMBOO_VERSION_FULL_BUILD;
	CHECK(full_build.begins_with("v" + String(BAMBOO_VERSION_STRING)));
	CHECK(full_build.contains("(Godot " + String(GODOT_VERSION_FULL_BUILD) + ")"));

	const String full_name = GODOT_VERSION_FULL_NAME;
	CHECK(full_name.begins_with(String(GODOT_VERSION_NAME) + " v" + String(BAMBOO_VERSION_STRING)));
	CHECK(full_name.ends_with(full_build));
}

TEST_CASE("[BambooVersion] Sprint 0.1.0-rc.1 values") {
	// Update this test case together with `version.py` when bumping the Bamboo version.
	CHECK_EQ(BAMBOO_VERSION_MAJOR, 0);
	CHECK_EQ(BAMBOO_VERSION_MINOR, 1);
	CHECK_EQ(BAMBOO_VERSION_PATCH, 0);
	CHECK_EQ(String(BAMBOO_VERSION_PRERELEASE), String("rc.1"));
	CHECK_EQ(String(BAMBOO_VERSION_CODENAME), String("Sprout"));
	CHECK_EQ(String(BAMBOO_VERSION_STRING), String("0.1.0-rc.1"));
	CHECK_EQ(String(GODOT_VERSION_NAME), String("Bamboo Engine"));
}

} // namespace TestBambooVersion
