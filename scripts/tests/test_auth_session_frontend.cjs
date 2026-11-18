// No browser session or network: exercise the actual service's document disposal.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname,
    '../../custom_addons/tp_web_login/static/src/js/session_guard.js'), 'utf8');
const serviceSource = source.slice(source.indexOf('export const tpSessionGuardService'),
    source.indexOf('registry.category("services")'))
    .replace('export const tpSessionGuardService', 'globalThis.service');

function harness() {
    const events = new Map();
    const calls = [];
    const document = {
        visibilityState: 'visible',
        documentElement: { style: {}, classList: { add() {} } },
        body: { classList: { add() {} } },
        querySelector: () => null,
        querySelectorAll: () => [{ replaceChildren() { calls.push('scrub'); },
            style: { setProperty() {} } }],
        addEventListener() {}, removeEventListener() {},
    };
    const context = {
        proxy: (x) => x,
        user: { userId: 7 }, session: { uid: 7, test_mode: true },
        SESSION_REPLACED_REASON: 'session_replaced', SESSION_CUTOVER_REASON: 'session_cutover',
        POLL_VISIBLE_MS: 4000, POLL_MAX_BACKOFF_MS: 30000,
        activeGuardInstance: null,
        rpcBus: { trigger() {}, addEventListener() {}, removeEventListener() {} },
        browser: {
            document, navigator: { onLine: true },
            location: {
                replace(url) {
                    assert.equal(document.documentElement.style.visibility, 'hidden');
                    assert.ok(calls.includes('scrub'));
                    calls.push(url);
                },
                reload() { calls.push('reload'); },
            },
            addEventListener: (name, fn) => events.set(name, fn),
            removeEventListener() {}, clearTimeout() {},
        },
    };
    vm.runInNewContext(serviceSource, context);
    return { guard: context.service.start({ services: {} }), events, calls, document };
}

const ended = harness();
ended.guard.enterEndedState('session_replaced');
ended.guard.enterEndedState('session_replaced');
assert.equal(ended.calls.filter((x) => x === '/tp/session-ended').length, 1);
assert.equal(ended.guard.state.ended, true);

const restored = harness();
restored.events.get('pagehide')();
assert.equal(restored.document.documentElement.style.visibility, 'hidden');
restored.events.get('pageshow')({ persisted: true });
assert.deepEqual(restored.calls, ['reload']);
assert.equal(restored.document.documentElement.style.visibility, 'hidden');
console.log('PASS: termination disposes webclient once; bfcache stays hidden until reload');
