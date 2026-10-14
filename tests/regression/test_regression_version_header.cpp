/**************************************************************************/
/*  test_regression_version_header.cpp                                    */
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

// BAMBOO: [Regression] BAMBOO-REG-1 - version macros generated from version.py stay usable from C++.

#include "tests/test_macros.h"

TEST_FORCE_LINK(test_regression_version_header)

#include "core/version.h"

namespace TestRegressionVersionHeader {

TEST_CASE("[Regression] BAMBOO-REG-1: generated version macros are valid string and integer literals") {
	const String bamboo_string = BAMBOO_VERSION_STRING;
	CHECK_FALSE(bamboo_string.is_empty());
	CHECK(bamboo_string.begins_with(itos(BAMBOO_VERSION_MAJOR) + "." + itos(BAMBOO_VERSION_MINOR) + "."));
	CHECK(String(GODOT_VERSION_FULL_NAME).contains(bamboo_string));
	CHECK(String(BAMBOO_VERSION_FULL_BUILD).contains(GODOT_VERSION_FULL_BUILD));
}

} // namespace TestRegressionVersionHeader
