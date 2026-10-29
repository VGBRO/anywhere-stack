const { test } = require('node:test');
const assert = require('node:assert/strict');
const merge = require('./index.cjs');

test('Expo config merges nested properties and concatenates arrays without mutation', () => {
  const target = { ios: { bundleIdentifier: 'com.example.app' }, plugins: [{ enabled: true }] };
  const source = { ios: { supportsTablet: true }, plugins: ['expo-router'] };
  const result = merge(target, source);
  assert.deepEqual(result, {
    ios: { bundleIdentifier: 'com.example.app', supportsTablet: true },
    plugins: [{ enabled: true }, 'expo-router'],
  });
  result.plugins[0].enabled = false;
  result.ios.bundleIdentifier = 'changed';
  assert.equal(target.plugins[0].enabled, true);
  assert.equal(target.ios.bundleIdentifier, 'com.example.app');
  assert.deepEqual(source.plugins, ['expo-router']);
});

test('prototype keys cannot poison the result from either input, including nested arrays', () => {
  const payload = JSON.parse('{"__proto__":{"polluted":true},"constructor":{"prototype":{"polluted":true}},"prototype":{"polluted":true},"nested":{"__proto__":{"polluted":true}},"items":[{"__proto__":{"polluted":true}}]}');
  for (const result of [merge({}, payload), merge(payload, {})]) {
    assert.equal(Object.getPrototypeOf(result), Object.prototype);
    assert.equal(result.polluted, undefined);
    assert.equal(Object.hasOwn(result, '__proto__'), false);
    assert.equal(Object.hasOwn(result, 'constructor'), false);
    assert.equal(Object.hasOwn(result, 'prototype'), false);
    assert.equal(Object.getPrototypeOf(result.nested), Object.prototype);
    assert.equal(result.nested.polluted, undefined);
    assert.equal(result.items[0].polluted, undefined);
  }
  assert.equal({}.polluted, undefined);
});

test('merge preserves enumerable symbols, dates, and source-overrides-target behavior', () => {
  const symbol = Symbol('config');
  const date = new Date('2026-01-01');
  const result = merge({ old: [1], flag: true }, { old: { next: 2 }, flag: undefined, date, [symbol]: 3 });
  assert.deepEqual(result.old, { next: 2 });
  assert.equal(result.flag, undefined);
  assert.equal(result.date, date);
  assert.equal(result[symbol], 3);
});

test('unsupported merge options fail explicitly instead of silently changing semantics', () => {
  assert.throws(() => merge({}, {}, { clone: false }), /does not support custom options/);
});
