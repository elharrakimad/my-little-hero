const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('analytics.js', 'utf8');

function run(dnt = '0', fail = false) {
  const requests = [], handlers = {};
  const context = {navigator: {doNotTrack: dnt}, location: {protocol: 'https:'},
    crypto: {randomUUID: () => 'f17dc52e-ff02-4b93-b81f-64507930a071'},
    sessionStorage: {getItem: () => null, setItem() {}}, window: {},
    document: {visibilityState: 'visible', addEventListener: (key, fn) => handlers[key] = fn},
    setInterval: fn => handlers.heartbeat = fn,
    fetch: (_, options) => {if (fail) throw new Error('offline'); requests.push(JSON.parse(options.body)); return Promise.resolve();}};
  vm.runInNewContext(source, context);
  handlers.DOMContentLoaded?.();
  return {context, requests, handlers};
}

test('counts a visit and visible heartbeat without collecting personal fields', () => {
  const {requests, handlers} = run();
  handlers.heartbeat();
  assert.deepEqual(requests.map(r => r.event_name), ['page_view', 'heartbeat']);
  assert.deepEqual(Object.keys(requests[0]).sort(), ['event_id', 'event_name', 'session_id']);
});
test('respects Do Not Track', () => assert.equal(run('1').requests.length, 0));
test('network failures cannot interrupt the customer flow', () => assert.doesNotThrow(() => run('0', true)));
