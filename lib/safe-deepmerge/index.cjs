// @expo/config only uses deepmerge(target, source), without custom options.
// Keep that call shape while replacing the unpatched prototype-poisoning code.
const merge = require('@fastify/deepmerge')({ symbols: true });

module.exports = function deepmerge(target, source, options) {
  if (options !== undefined) {
    throw new TypeError('The Expo merge adapter does not support custom options');
  }
  return merge(target, source);
};
