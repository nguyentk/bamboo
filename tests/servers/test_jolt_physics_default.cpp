/**************************************************************************/
/*  test_jolt_physics_default.cpp                                         */
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

// BAMBOO: Tests that Jolt Physics is the 3D physics engine for new projects, while existing
// projects keep the engine they are configured with.

#include "tests/test_macros.h"

TEST_FORCE_LINK(test_jolt_physics_default)

#include "servers/physics_3d/physics_server_3d_manager.h"

#include "modules/modules_enabled.gen.h" // For jolt_physics, godot_physics_3d.

#ifdef TOOLS_ENABLED
#include "editor/editor_node.h"
#endif

namespace TestJoltPhysicsDefault {

#ifdef MODULE_JOLT_PHYSICS_ENABLED

TEST_CASE("[JoltPhysics] Jolt Physics is registered as a 3D physics server") {
	PhysicsServer3DManager *manager = PhysicsServer3DManager::get_singleton();
	REQUIRE(manager != nullptr);
	const int jolt_id = manager->find_server_id(PhysicsServer3DManager::JOLT_PHYSICS_NAME);
	CHECK(jolt_id != -1);
	CHECK_EQ(manager->get_server_name(jolt_id), String("Jolt Physics"));
}

#ifdef TOOLS_ENABLED
TEST_CASE("[JoltPhysics] New projects default to Jolt Physics") {
	// Initial settings written by the project manager (and for empty project.godot files).
	const HashMap<String, Variant> settings = EditorNode::get_initial_settings();
	REQUIRE(settings.has("physics/3d/physics_engine"));
	CHECK_EQ(String(settings["physics/3d/physics_engine"]), String(PhysicsServer3DManager::JOLT_PHYSICS_NAME));
}
#endif // TOOLS_ENABLED

#ifdef MODULE_GODOT_PHYSICS_3D_ENABLED
TEST_CASE("[JoltPhysics] Existing projects keep their configured engine") {
	PhysicsServer3DManager *manager = PhysicsServer3DManager::get_singleton();
	// A project explicitly configured with GodotPhysics3D still resolves to it.
	const int godot_id = manager->find_server_id(PhysicsServer3DManager::GODOT_PHYSICS_3D_NAME);
	REQUIRE(godot_id != -1);
	CHECK(godot_id != manager->find_server_id(PhysicsServer3DManager::JOLT_PHYSICS_NAME));

	// "DEFAULT" (projects created before Jolt became the new-project default) is not a server
	// name, so PhysicsServer3DManager::initialize_server() falls back to the default server
	// (GodotPhysics3D) for them. Creating servers here would replace the global
	// PhysicsServer3D singleton used by the test runner; the runtime fallback is covered by
	// tests/python_build/test_jolt_physics_integration.py.
	CHECK_EQ(manager->find_server_id("DEFAULT"), -1);
}
#endif // MODULE_GODOT_PHYSICS_3D_ENABLED

#endif // MODULE_JOLT_PHYSICS_ENABLED

} // namespace TestJoltPhysicsDefault
