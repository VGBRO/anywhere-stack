const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { resolve } = require('node:path');

const mobile = createRequire(resolve(__dirname, '../../artifacts/anywhere-mobile/package.json'));
const expo = createRequire(mobile.resolve('expo/package.json'));

test('Expo actually resolves the safe merger and loads its config', () => {
  const config = createRequire(expo.resolve('@expo/config'));
  // pnpm file: dependencies are installed copies, not the same module object.
  assert.equal(config('deepmerge/package.json').name, '@workspace/safe-deepmerge');
  const merged = config('deepmerge')({}, JSON.parse('{"__proto__":{"polluted":true},"plugins":["expo-router"]}'));
  assert.equal(merged.polluted, undefined);
  assert.deepEqual(merged.plugins, ['expo-router']);
  const { getConfig } = expo('@expo/config');
  const { exp } = getConfig(resolve(__dirname, '../../artifacts/anywhere-mobile'));
  assert.equal(exp.name, 'Anywhere Stack');
  assert.equal(exp.slug, 'anywhere-mobile');
});

test('Expo Router query-string keeps CommonJS parse/stringify semantics with the fixed decoder', () => {
  const router = createRequire(mobile.resolve('expo-router/package.json'));
  const query = router('query-string');
  const queryRequire = createRequire(router.resolve('query-string'));
  assert.equal(queryRequire('decode-uri-component/package.json').name, '@workspace/safe-uri-decoder');
  assert.deepEqual({ ...query.parse('project=hello%20world&tag=a&tag=b&bad=%zz') }, {
    bad: '%zz', project: 'hello world', tag: ['a', 'b'],
  });
  assert.equal(query.stringify({ project: 'hello world' }), 'project=hello%20world');
});

test('Expo CLI schemas load and validate with patched Zod 4', () => {
  const cli = createRequire(expo.resolve('@expo/cli/package.json'));
  const { PluginSchema } = cli('./build/src/start/server/DevToolsPlugin.schema.js');
  assert.equal(cli('zod/package.json').version.split('.')[0], '4');
  assert.equal(PluginSchema.safeParse({}).success, false);
});
