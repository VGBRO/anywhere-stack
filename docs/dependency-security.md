# Dependency security maintenance

Install reproducibly with `pnpm install --frozen-lockfile` and
`uv sync --frozen`. Run `pnpm test` and `pnpm run typecheck` after updates.
Use a dependency audit as well: regression tests exercise specific failure
cases, not every published advisory.

## Python

The root and `.migration-backup/` environments both require
`certifi>=2026.10.19` and `pyjwt>=2.15.0`. Both lockfiles contain patched
releases. The backup remains reference-only, excluded from deployments, but
must not restore a known-vulnerable environment.

## JavaScript

The workspace catalog and overrides require patched Zod 4 for both direct and
transitive consumers. Form resolvers and Zod error formatting dependencies
were upgraded for Zod 4 compatibility. Shared React type declarations use
the same 19.2 series as the mobile app, avoiding incompatible UI ref types.

Overrides also establish patched floors for body-parser, qs, undici,
node-forge, fast-uri, and the 6.x postcss-selector-parser used by typography.
The direct parents still allow or pin affected versions, so retain these
floors until their dependency ranges exclude the vulnerable releases.
The one-day package release-age protection remains enabled.

Two narrow compatibility adapters are used instead of upgrading the Expo SDK:

- `@expo/config > deepmerge` resolves to `@workspace/safe-deepmerge`.
  There is no patched upstream deepmerge release. The adapter uses
  `@fastify/deepmerge`, which rejects prototype-related keys, preserves the
  two-argument calls Expo makes, clones nested values, and concatenates arrays.
  Unsupported custom options fail explicitly. If Expo changes its usage,
  update the adapter and its tests before updating Expo.
- `query-string > decode-uri-component` resolves to
  `@workspace/safe-uri-decoder`. This exposes the patched ESM decoder's
  default export as the CommonJS callable expected by query-string 7.
  Node 24 supports synchronous ESM loading; Metro also understands the
  underlying ESM module. Do not override the decoder globally to this adapter,
  because the adapter itself depends on the real patched decoder.

`pnpm test` covers prototype poisoning, malformed URI decoding performance,
Expo's actual config and router dependency resolution, Expo CLI Zod schema
loading, deeply nested JWT payloads, and inconsistent Ed25519/Ed448 JWKs,
alongside the existing API and browser tests. The pre-existing partial-sync
TODO is unrelated to dependencies and remains unchanged.
