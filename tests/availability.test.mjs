import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import test from 'node:test';

test('failure preserves input, never replays POST, and online alone cannot dismiss', async () => {
  class Element {
    constructor() { this.children = []; this.listeners = {}; this.hidden = false; }
    setAttribute() {}
    append(...children) { this.children.push(...children); }
    prepend(child) { this.children.unshift(child); }
    addEventListener(name, callback) { this.listeners[name] = callback; }
    removeEventListener(name) { delete this.listeners[name]; }
    remove() {}
  }
  const events = {};
  globalThis.addEventListener = (name, fn) => { events[name] = fn; };
  globalThis.removeEventListener = name => { delete events[name]; };
  const body = new Element();
  const input = {value: 'unsaved draft'};
  body.append(input);
  globalThis.document = {body, createElement: () => new Element()};
  const source = await readFile(new URL('../src/mobile_foundation/static/mf/availability.js', import.meta.url), 'utf8');
  const {createAvailability} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  const calls = [];
  let result = {status: 503, ok: false};
  const ui = createAvailability({probeUrl: '/health', fetcher: async (...args) => {
    calls.push(args);
    if (result instanceof Error) throw result;
    return result;
  }});
  const options = {method: 'POST', body: 'order'};
  assert.equal(await ui.request('/api/orders', options), result);
  const banner = body.children[0];
  assert.equal(banner.hidden, false);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][1], options);
  assert.equal(body.children[1], input);
  assert.equal(input.value, 'unsaved draft');
  assert.equal(events.online, undefined);
  result = new Error('connection refused');
  await assert.rejects(ui.request('/api/orders', options));
  assert.equal(calls.length, 2);
  result = {status: 200, ok: true};
  await banner.children[1].listeners.click();
  assert.equal(calls[2][0], '/health');
  assert.equal(calls[2][1].method, 'GET');
  assert.equal(banner.hidden, true);
  result = new DOMException('user cancel', 'AbortError');
  await assert.rejects(ui.request('/api/orders', options));
  assert.equal(banner.hidden, true);
  events.offline();
  assert.equal(banner.hidden, false);
  ui.dispose();
  assert.equal(events.offline, undefined);
});
