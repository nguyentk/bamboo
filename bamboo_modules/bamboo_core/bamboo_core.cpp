/**************************************************************************/
/*  bamboo_core.cpp                                                       */
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

#include "bamboo_core.h"

#include "core/object/class_db.h"
#include "core/version.h"

BambooCore *BambooCore::singleton = nullptr;

void BambooCore::_bind_methods() {
	ClassDB::bind_method(D_METHOD("get_version_string"), &BambooCore::get_version_string);
	ClassDB::bind_method(D_METHOD("get_codename"), &BambooCore::get_codename);
	ClassDB::bind_method(D_METHOD("get_godot_base_version"), &BambooCore::get_godot_base_version);
	ClassDB::bind_method(D_METHOD("get_version_info"), &BambooCore::get_version_info);
}

String BambooCore::get_version_string() const {
	return BAMBOO_VERSION_STRING;
}

String BambooCore::get_codename() const {
	return BAMBOO_VERSION_CODENAME;
}

String BambooCore::get_godot_base_version() const {
	return GODOT_VERSION_FULL_CONFIG;
}

Dictionary BambooCore::get_version_info() const {
	Dictionary info;
	info["major"] = BAMBOO_VERSION_MAJOR;
	info["minor"] = BAMBOO_VERSION_MINOR;
	info["patch"] = BAMBOO_VERSION_PATCH;
	info["prerelease"] = BAMBOO_VERSION_PRERELEASE;
	info["codename"] = BAMBOO_VERSION_CODENAME;
	info["string"] = BAMBOO_VERSION_STRING;
	info["godot_base"] = GODOT_VERSION_FULL_CONFIG;
	return info;
}

BambooCore::BambooCore() {
	singleton = this;
}

BambooCore::~BambooCore() {
	singleton = nullptr;
}
