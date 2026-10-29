import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { strict as assert } from "node:assert";
import { test } from "node:test";
import vm from "node:vm";

const html = readFileSync(new URL("../public/mobile-source.html", import.meta.url), "utf8");

test("mobile snapshot is the exact requested GitHub Liquid Glass interface", () => {
  assert.equal(createHash("sha256").update(html).digest("hex"),
    "8f04a0d39e0b25c92a933244913b9add1ee9a510dd7ff569fac2d324a091913d");
  assert.ok(html.includes("Your intelligence, everywhere"));
  assert.ok(html.includes('id="s-arrival"'));
  assert.ok(html.includes('id="s-work"'));
  for (const script of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    assert.doesNotThrow(() => new vm.Script(script[1]));
  }
});

test("both mobile platforms load the pinned snapshot instead of the web home", () => {
  const config = readFileSync(new URL("../../anywhere-mobile/constants/sourceApp.ts", import.meta.url), "utf8");
  assert.ok(config.includes("/mobile-source.html?source=00ef0ce"));
  for (const filename of ["SourceAppScreen.tsx", "SourceAppScreen.web.tsx"]) {
    const wrapper = readFileSync(new URL(`../../anywhere-mobile/components/${filename}`, import.meta.url), "utf8");
    assert.ok(wrapper.includes("sourceAppUrl"));
  }
});

test("upstream work and personal filters preserve project detail indexes", () => {
  const nodes = new Map();
  const context = vm.createContext({
    document: {
      getElementById(id) {
        if (!nodes.has(id)) nodes.set(id, { innerHTML: "" });
        return nodes.get(id);
      },
      createElement() {
        return {
          style: { setProperty() {} },
          setAttribute(key, value) { this[key] = value; },
          get outerHTML() { return `<div onclick="${this.onclick}">${this.innerHTML}</div>`; },
        };
      },
    },
    esc: String,
  });
  vm.runInContext(
    html.slice(html.indexOf("var projects ="), html.indexOf("function esc(")) +
    html.slice(html.indexOf("function renderHomeProjList("), html.indexOf("function buildHomeSections(")),
    context,
  );
  context.renderHomeProjList("firmos");
  const work = nodes.get("hp-project-list").innerHTML;
  assert.equal((work.match(/onclick=/g) || []).length, 4);
  assert.ok(!work.includes("Telugu Thriller"));
  context.renderHomeProjList("personal");
  const personal = nodes.get("hp-project-list").innerHTML;
  assert.ok(personal.includes("Telugu Thriller"));
  assert.ok(personal.includes('onclick="openProject(3)"'));
  context.renderHomeProjList("offline");
  assert.equal((nodes.get("hp-project-list").innerHTML.match(/CACHED/g) || []).length, 5);
});

function voiceLoginPage(SpeechRecognition) {
  const nodes = new Map();
  const timeouts = [];
  const intervals = new Map();
  const context = vm.createContext({
    window: { SpeechRecognition },
    document: {
      getElementById(id) {
        if (!nodes.has(id)) {
          const classes = new Set();
          nodes.set(id, {
            textContent: "", style: {}, classes,
            classList: {
              add(...items) { items.forEach(item => classes.add(item)); },
              remove(...items) { items.forEach(item => classes.delete(item)); },
            },
          });
        }
        return nodes.get(id);
      },
    },
    setTimeout(fn) { timeouts.push(fn); return fn; },
    clearTimeout(fn) { const i = timeouts.indexOf(fn); if (i >= 0) timeouts.splice(i, 1); },
    setInterval(fn) { intervals.set(fn, fn); return fn; },
    clearInterval(fn) { intervals.delete(fn); },
    buildHomeSections() { context.builtHome = true; },
    showScreen(id) { context.screen = id; },
  });
  vm.runInContext(
    html.slice(html.indexOf("var authRecognition="), html.indexOf("function goHome(")),
    context,
  );
  return {
    context, nodes,
    finish() {
      for (let i = 0; i < 3; i++) [...intervals.values()].forEach(fn => fn());
      while (timeouts.length) timeouts.shift()();
    },
  };
}

test("upstream voice login shows its overlay and completes its unsupported-browser demo", () => {
  const { context, nodes, finish } = voiceLoginPage();
  context.doVoiceAuth();
  assert.ok(nodes.get("arrival-listen").classes.has("active"));
  assert.ok(nodes.get("auth-orb").classes.has("listening"));
  for (const id of ["arrival-symbol", "arrival-name", "arrival-tagline"]) {
    assert.ok(nodes.get(id).classes.has("arrival-hide"));
  }
  finish();
  assert.equal(context.screen, "s-home");
  assert.equal(context.builtHome, true);
  assert.ok(!nodes.get("arrival-listen").classes.has("active"));
  for (const id of ["arrival-symbol", "arrival-name", "arrival-tagline"]) {
    assert.ok(!nodes.get(id).classes.has("arrival-hide"));
  }
});

test("upstream voice login handles recognized speech and microphone-denied demo paths", () => {
  for (const denied of [false, true]) {
    let recognizer;
    class Recognition {
      constructor() { recognizer = this; }
      start() {}
      stop() {}
    }
    const { context, finish } = voiceLoginPage(Recognition);
    context.doVoiceAuth();
    if (denied) recognizer.onerror({ error: "not-allowed" });
    else {
      const result = [{ transcript: "Hello Anywhere" }];
      result.isFinal = true;
      recognizer.onresult({ results: [result] });
    }
    finish();
    assert.equal(context.screen, "s-home");
  }
});

test("upstream voice login cancel stops recognition and restores arrival controls", () => {
  let stopped = false;
  class Recognition {
    start() {}
    stop() { stopped = true; }
  }
  const { context, nodes } = voiceLoginPage(Recognition);
  context.doVoiceAuth();
  context.cancelVoiceAuth();
  assert.equal(stopped, true);
  assert.ok(!nodes.get("arrival-listen").classes.has("active"));
  assert.ok(!nodes.get("arrival-btns").classes.has("hidden"));
  for (const id of ["arrival-symbol", "arrival-name", "arrival-tagline"]) {
    assert.ok(!nodes.get(id).classes.has("arrival-hide"));
  }
});

test("voice completion uses the upstream personalized welcome", () => {
  const { context, nodes } = voiceLoginPage();
  context.completeVoiceAuth();
  assert.equal(nodes.get("auth-status").textContent, "Voice confirmed. Welcome back, VG!");
});
