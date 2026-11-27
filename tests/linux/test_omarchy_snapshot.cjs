const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const { runInNewContext } = require("node:vm");
const test = require("node:test");

const model = {};
runInNewContext(readFileSync(resolve(__dirname, "../../nauta_monitor/platform/linux/omarchy/Snapshot.js"), "utf8"), model);

const markup = '<img src="https://example.invalid/tracker">';
const zero = {
  version: 1,
  credit_cup: 0,
  hours: 0,
  account_status: markup,
  last_success_at: 1000,
  last_attempt_at: 1000,
  result: "ok",
  stale_after_seconds: 180,
};
const parse = (value) => model.parse(JSON.stringify(value));

test("zero, missing, stale and failed results stay distinct", () => {
  const latest = parse(zero);
  assert.equal(latest.credit_cup, 0);
  assert.equal(model.hoursLabel(latest.hours, String), "0 h");
  assert.equal(model.hoursLabel(12.59, String), "12 h 35 m");
  assert.equal(model.freshness(null, 1000), "noData");
  assert.equal(model.freshness(latest, 1180), "fresh");
  assert.equal(model.freshness(latest, 1181), "stale");
  assert.equal(model.freshness(parse({ ...zero, result: "error", last_attempt_at: 1120 }), 1120), "error");
  assert.equal(model.freshness(parse({
    ...zero, result: "error", last_success_at: null, hours: null, credit_cup: null, account_status: null,
  }), 1000), "errorNoData");
});

test("invalid and oversized snapshots are not displayed", () => {
  assert.equal(model.parse("{"), null);
  for (const fields of [
    { version: 2 }, { hours: "0" }, { credit_cup: -1 }, { account_status: "x".repeat(257) },
    { last_success_at: null }, { last_attempt_at: 999 }, { ignored: "x".repeat(4096) },
  ]) assert.equal(parse({ ...zero, ...fields }), null);
});

test("portal text is rendered by the plugin's plain-text component", () => {
  const qml = readFileSync(resolve(__dirname, "../../nauta_monitor/platform/linux/omarchy/BarWidget.qml"), "utf8");
  assert.equal(parse(zero).account_status, markup);
  assert.match(qml, /Detail\s*\{\s*text:[^\n]+account_status/);
  assert.match(qml, /component Detail: Text\s*\{[^}]+textFormat: Text\.PlainText/);
});

test("the activity log has its own six-line scrolling viewport", () => {
  const qml = readFileSync(resolve(__dirname, "../../nauta_monitor/platform/linux/omarchy/BarWidget.qml"), "utf8");
  assert.match(qml, /contentHeight: fittedContentHeight\(loadedContentHeight, Commons\.Style\.space\(520\)\)/);
  assert.match(qml, /id: activityLogView[\s\S]*?height: Commons\.Style\.space\(144\)/);
  assert.match(qml, /id: activityLogView[\s\S]*?ScrollBar\.vertical: ScrollBar \{ policy: ScrollBar\.AsNeeded \}/);
  assert.doesNotMatch(qml, /Flickable\s*\{\s*anchors\.fill: parent/);
});
