const { test } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const decode = require('./index.cjs');

test('the fixed decoder remains callable from CommonJS and tolerates malformed input', () => {
  assert.equal(typeof decode, 'function');
  assert.equal(decode('%C3%A5%20hello'), 'å hello');
  assert.equal(decode('ordinary text'), 'ordinary text');
  assert.equal(decode('%zz'), '%zz');
  assert.equal(decode('a%20b%zz'), 'a b%zz');
});

test('many distinct malformed percent runs finish without quadratic blocking', () => {
  const result = spawnSync(process.execPath, ['-e', `
    const decode = require(${JSON.stringify(__filename.replace('test.cjs', 'index.cjs'))});
    let input = '';
    for (let i = 0; i < 32000; i++) {
      input += '%' + Math.floor(i / 256).toString(16).padStart(2, '0')
        + '%' + (i % 256).toString(16).padStart(2, '0') + 'x';
    }
    decode(input + '%zz');
    decode('%C1'.repeat(40000));
  `], { timeout: 5000, encoding: 'utf8' });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
});
