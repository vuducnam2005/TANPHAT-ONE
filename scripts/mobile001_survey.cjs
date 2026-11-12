/* MOBILE-001 read-only responsive survey of native Odoo routes; credentials/evidence stay in .local. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const target = args[0] || 'dev';
const label = args[1] || 'survey';
assert(['clone', 'dev'].includes(target));
const owner = JSON.parse(fs.readFileSync(path.join(root, '.local/dash-ui001/owner.json'), 'utf8'));
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const secrets = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json'), 'utf8'));
const actors = JSON.parse(fs.readFileSync(path.join(root, '.local/native-data003/actor-secrets.json'), 'utf8'));
const out = path.join(root, '.local/mobile001', `${label}-${target}`);
fs.mkdirSync(out, { recursive: true });

const VIEWPORTS = (process.env.TP_VIEWPORTS || '360x800,390x844,1440x900').split(',').map(v => {
  const [width, height] = v.split('x').map(Number);
  return { width, height };
});
const ACTORS = (process.env.TP_ACTORS || 'admin,long,son').split(',');
const ROUTES = [
  ['home', '/odoo/tp-home', '.o_tp_web_home_tile'],
  ['dash-finance', '/odoo/dashboards?dashboard_id=6', '.tp_connected_dashboard, .o_spreadsheet_dashboard_action'],
  ['dash-coord', '/odoo/dashboards?dashboard_id=5', '.tp_connected_dashboard, .o_spreadsheet_dashboard_action'],
  ['projects', '/odoo/project', '.o_kanban_record, .o_view_nocontent'],
  ['tp-projects', '/odoo/action-tp_project.action_tp_projects', '.o_data_row, .o_view_nocontent'],
  ['tasks', '/odoo/action-project.action_view_all_task', '.o_kanban_record, .o_data_row, .o_view_nocontent'],
  ['timesheets', '/odoo/timesheets', '.o_data_row, .o_kanban_record, .o_view_nocontent, .o_timesheet_grid'],
  ['expenses', '/odoo/expenses', '.o_data_row, .o_view_nocontent, .o_kanban_record'],
  ['crm', '/odoo/crm', '.o_kanban_record, .o_view_nocontent'],
  ['contacts', '/odoo/contacts', '.o_kanban_record, .o_data_row, .o_view_nocontent'],
  ['employees', '/odoo/employees', '.o_kanban_record, .o_data_row, .o_view_nocontent'],
  ['invoices', '/odoo/action-account.action_move_out_invoice_type', '.o_data_row, .o_view_nocontent, .o_kanban_record'],
];
const ONLY = process.env.TP_ROUTES ? new Set(process.env.TP_ROUTES.split(',')) : null;

async function login(browser, key, viewport) {
  const isMobile = viewport.width < 768;
  const context = await browser.newContext({ viewport, isMobile, hasTouch: isMobile, deviceScaleFactor: 1, locale: 'vi-VN' });
  const credentials = key === 'admin' ? { login: 'admin', password: secrets.admin } : actors[key];
  const response = await context.request.post(`${base}/web/session/authenticate`, {
    data: { jsonrpc: '2.0', method: 'call', params: { db, ...credentials } },
  });
  assert((await response.json()).result?.uid, `${key} login failed`);
  return context;
}

/* Layout facts read from the rendered page; not a substitute for viewing the screenshot. */
function measure() {
  const vw = window.innerWidth;
  const visible = el => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.visibility !== 'hidden' && s.display !== 'none' && r.width > 0 && r.height > 0;
  };
  const clipped = el => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) return p.getBoundingClientRect().right <= vw + 1;
    }
    return false;
  };
  const name = el => `${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.') : ''}`;
  const overflowing = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 && !clipped(el)) overflowing.push(`${name(el)} right=${Math.round(r.right)}`);
  }
  const smallTargets = [];
  for (const el of document.querySelectorAll('a[href], button, input:not([type=hidden]), select, [role=button], .o_searchview_input')) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight * 3) continue;
    if (r.width < 32 || r.height < 32) smallTargets.push(`${name(el)} ${Math.round(r.width)}x${Math.round(r.height)} "${(el.innerText || el.getAttribute('aria-label') || el.title || '').trim().slice(0, 30)}"`);
  }
  let tinyText = 0;
  const tinySamples = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!visible(el) || ![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (size < 12) { tinyText += 1; if (tinySamples.length < 8) tinySamples.push(`${name(el)} ${size}px "${el.textContent.trim().slice(0, 24)}"`); }
  }
  return {
    metaViewport: document.querySelector('meta[name=viewport]')?.content || null,
    innerWidth: vw, scrollWidth: document.documentElement.scrollWidth,
    pageOverflow: document.documentElement.scrollWidth > vw,
    overflowing: overflowing.slice(0, 12), overflowCount: overflowing.length,
    smallTargets: smallTargets.slice(0, 15), smallTargetCount: smallTargets.length,
    tinyText, tinySamples,
    uiSize: document.body.className.match(/o_(xs|sm|md|lg|xl|xxl)?\w*/)?.[0] || null,
    title: document.title,
  };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const report = [];
  try {
    for (const actor of ACTORS) {
      for (const viewport of VIEWPORTS) {
        const context = await login(browser, actor, viewport);
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', e => errors.push(e.message));
        page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
        for (const [key, url, ready] of ROUTES) {
          if (ONLY && !ONLY.has(key)) continue;
          errors.length = 0;
          const row = { actor, viewport: `${viewport.width}x${viewport.height}`, key, url };
          try {
            await page.goto(base + url, { waitUntil: 'domcontentloaded' });
            await page.locator(`${ready}, .o_error_dialog, .o_action_manager .o_view_nocontent, .o_notification`).filter({ visible: true }).first().waitFor({ timeout: 20000 });  // skip hidden kanban ghost cards
            await page.waitForTimeout(900);
            row.denied = await page.locator('.o_error_dialog, .o_dialog_error').count() > 0;
            Object.assign(row, await page.evaluate(measure));
            await page.screenshot({ path: path.join(out, `${actor}-${key}-${viewport.width}.png`) });
          } catch (error) {
            row.failed = error.message.split('\n')[0];
            await page.screenshot({ path: path.join(out, `${actor}-${key}-${viewport.width}-failed.png`) }).catch(() => {});
          }
          row.errors = [...errors];
          report.push(row);
          console.log(JSON.stringify({ actor: row.actor, vp: row.viewport, key, failed: row.failed, denied: row.denied,
            overflow: row.pageOverflow, oc: row.overflowCount, small: row.smallTargetCount, tiny: row.tinyText, err: row.errors.length }));
        }
        await context.close();
      }
    }
  } finally {
    fs.writeFileSync(path.join(out, 'survey.json'), JSON.stringify(report, null, 2));
    await browser.close();
  }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
