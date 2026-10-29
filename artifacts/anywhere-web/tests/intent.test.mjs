// Exercise the original page's request handlers without a browser or live provider.
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { strict as assert } from "node:assert";
import { test } from "node:test";
import vm from "node:vm";

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const intent = html.slice(html.indexOf("async function processIntent("), html.indexOf("function applyBrain("));
const sync = html.slice(html.indexOf("async function flushQueue("), html.indexOf("// ── FirmOS"));

test("the interface matches the original page with the scoped upstream pill/filter update", () => {
  // Original interface plus the requested Firm OS/filter backport, not the
  // unrelated arrival, presence, and work-screen redesign in newer upstream.
  assert.equal(
    createHash("sha256").update(html).digest("hex"),
    "ae24cfff211efde75b5b867939bb18b13de1fb8938da1033e800a6f525d47dc5",
  );
});

function filterPage() {
  const nodes = new Map();
  function element() {
    return {
      innerHTML: "", textContent: "", children: [], style: {}, attributes: {},
      classList: { toggle() {} },
      setAttribute(key, value) { this.attributes[key] = value; },
      appendChild(child) { this.children.push(child); },
    };
  }
  const context = vm.createContext({
    document: {
      getElementById(id) {
        if (!nodes.has(id)) nodes.set(id, element());
        return nodes.get(id);
      },
      createElement: element,
      body: element(),
    },
    setIS() {}, showBanner() {}, hideBanner() {}, flushQueue() {}, toast() {},
    setTimeout() {},
    openSheet(index) { context.openedIndex = index; },
  });
  vm.runInContext(
    html.slice(html.indexOf("let isOnline="), html.indexOf("// ── Navigation")) +
    html.slice(html.indexOf("function renderProjects()"), html.indexOf("function openSheet(")) +
    html.slice(html.indexOf("function toggleOnline()"), html.indexOf("async function flushQueue(")) +
    html.slice(html.indexOf("function toggleFirmOS()"), html.indexOf("// ── Utils")),
    context,
  );
  function render() {
    const list = context.document.getElementById("projects-list");
    // Mirror DOM innerHTML clearing its children.
    list.children = [];
    context.renderProjects();
    return list.children;
  }
  return { context, render, nodes };
}

test("Firm OS filters work projects and preserves original detail indexes", () => {
  const { context, render, nodes } = filterPage();
  assert.equal(render().length, 5);
  context.toggleFirmOS();
  const work = render();
  assert.equal(work.length, 3);
  assert.ok(work.every(card => card.innerHTML.includes('scope-badge work')));
  work[0].onclick();
  assert.equal(context.openedIndex, 1); // India, not the hidden ADU at index zero.
  assert.equal(nodes.get("firm-btn").textContent, "Personal");
  assert.equal(nodes.get("firm-btn").attributes["aria-pressed"], "true");
  context.toggleFirmOS();
  assert.equal(render().length, 5);
  assert.equal(nodes.get("firm-btn").textContent, "Firm OS");
  assert.equal(nodes.get("firm-btn").attributes["aria-pressed"], "false");
});

test("offline and Firm OS filters compose in either toggle order", () => {
  const { context, render } = filterPage();
  context.toggleOnline();
  assert.ok(render().every(card => card.innerHTML.includes("CACHED")));
  context.toggleFirmOS();
  assert.equal(render().length, 3);
  assert.ok(render().every(card => card.innerHTML.includes("CACHED")));
  context.toggleOnline();
  assert.equal(render().length, 3);
  assert.ok(render().every(card => !card.innerHTML.includes("CACHED")));
  context.toggleOnline();
  context.toggleFirmOS();
  assert.equal(render().length, 5);
  assert.ok(render().every(card => card.innerHTML.includes("CACHED")));
});

function page(fetch) {
  const context = vm.createContext({
    fetch, API_BASE: "", projects: [], offlineQueue: [], updates: [], messages: [],
    setIS() {}, toast(message) { context.messages.push(message); },
    showBanner() {}, hideBanner() {}, setTimeout(fn) { fn(); },
    applyBrain(data) { context.updates.push(data); },
  });
  vm.runInContext(intent + sync, context);
  return context;
}

test("successful intent sends the existing contract and applies its real response", async () => {
  const state = page(async (url, options) => {
    assert.equal(url, "/api/intent");
    assert.deepEqual(JSON.parse(options.body), { text: "Plan work", projects: [] });
    return { ok: true, json: async () => ({ response: "Done", brain: { state: "Planned" } }) };
  });
  await state.processIntent("Plan work");
  assert.equal(state.updates.length, 1);
  assert.equal(state.offlineQueue.length, 0);
});

test("upstream provider-error fallback captures a local project update", async () => {
  const state = page(async () => ({ ok: false, status: 502 }));
  state.projects = [{ id: "work", name: "Work", goal: "Plan", state: "Ready", decision: "Start", actions: [], memory: "" }];
  await state.processIntent("Plan work");
  assert.equal(state.updates.length, 1);
  assert.equal(state.updates[0].brain.state, 'Intent captured: "Plan work"');
  assert.equal(state.messages.at(-1), "Saved locally.");
});

test("upstream partial sync applies only processed responses", async () => {
  const state = page(async () => ({
    ok: true, json: async () => ({ synced: 2, results: [
      { id: "one", status: "processed", brain: { state: "Planned" } },
      { id: "two", status: "error", error: "AI unavailable" },
    ] }),
  }));
  state.offlineQueue = [{ id: "one", text: "First" }, { id: "two", text: "Second" }];
  await state.flushQueue();
  assert.equal(state.updates.length, 1);
  assert.equal(state.updates[0].id, "one");
});

test("upstream network sync failure reports an error without applying results", async () => {
  const state = page(async () => { throw new Error("offline"); });
  state.offlineQueue = [{ id: "one", text: "First" }];
  await state.flushQueue();
  assert.equal(state.updates.length, 0);
  assert.equal(state.messages.at(-1), "Sync failed — will retry.");
});

// Known upstream limitations; changing them requires approval to diverge from
// the user's explicit as-is requirement, rather than silently redesigning it.
test.todo("Retain unprocessed session queue entries after a partial or failed sync");
