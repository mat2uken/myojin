// Copyright 2013 The Closure Library Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Unit tests for goog.json.hybrid.
 * @author nnaze@google.com (Nathan Naze)
 */

goog.provide('goog.json.hybridTest');

goog.require('goog.json');
goog.require('goog.json.hybrid');
goog.require('goog.testing.PropertyReplacer');
goog.require('goog.testing.jsunit');
goog.require('goog.testing.recordFunction');
goog.require('goog.userAgent');

goog.setTestOnly('goog.json.hybridTest');


var propertyReplacer = new goog.testing.PropertyReplacer();

var jsonParse;
var jsonStringify;
var googJsonUnsafeParse;
var googJsonSerialize;

function isIe7() {
  return goog.userAgent.IE && !goog.userAgent.isVersionOrHigher('8');
}

function setUp() {
  googJsonUnsafeParse = goog.testing.recordFunction(goog.json.unsafeParse);
  googJsonSerialize = goog.testing.recordFunction(goog.json.serialize);
  propertyReplacer.set(goog.json, 'unsafeParse', googJsonUnsafeParse);
  propertyReplacer.set(goog.json, 'serialize', googJsonSerialize);

  jsonParse = goog.testing.recordFunction(
      goog.global.JSON && goog.global.JSON.parse);
  jsonStringify = goog.testing.recordFunction(
      goog.global.JSON && goog.global.JSON.stringify);

  if (goog.global.JSON) {
    propertyReplacer.set(goog.global.JSON, 'parse', jsonParse);
    propertyReplacer.set(goog.global.JSON, 'stringify', jsonStringify);
  }
}

function tearDown() {
  propertyReplacer.reset();
}

function parseJson() {
  var obj = goog.json.hybrid.parse('{"a": 2}');
  assertObjectEquals({'a': 2}, obj);
}

function serializeJson() {
  var str = goog.json.hybrid.stringify({b: 2});
  assertEquals('{"b":2}', str);
}

function testNativeJsonPresent() {
  // No native JSON in IE7
  if (isIe7()) {
    return;
  }

  parseJson();
  serializeJson();

  assertEquals(1, jsonParse.getCallCount());
  assertEquals(1, jsonStringify.getCallCount());
  assertEquals(0, googJsonUnsafeParse.getCallCount());
  assertEquals(0, googJsonSerialize.getCallCount());
}

function testNativeJsonAbsent() {
  propertyReplacer.set(goog.global, 'JSON', null);

  parseJson();
  serializeJson();

  assertEquals(0, jsonParse.getCallCount());
  assertEquals(0, jsonStringify.getCallCount());
  assertEquals(1, googJsonUnsafeParse.getCallCount());
  assertEquals(1, googJsonSerialize.getCallCount());
}

function testCurrentBrowser() {
  parseJson();
  serializeJson();

  assertEquals(isIe7() ? 0 : 1, jsonParse.getCallCount());
  assertEquals(isIe7() ? 0 : 1, jsonStringify.getCallCount());
  assertEquals(isIe7() ? 1 : 0, googJsonUnsafeParse.getCallCount());
  assertEquals(isIe7() ? 1 : 0, googJsonSerialize.getCallCount());
}

