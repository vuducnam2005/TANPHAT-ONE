/* KD-UI-004 Overview checks, called by kd_ui004_ui.cjs (after on the clone, verify on dev 18069).
 *
 * Every number on screen is compared with the tp.kd.overview payload of the same actor and with the
 * search_count of the server drill-down domain (action_kd_open). Network mocks (late answer, failed
 * refresh, access error, no-permission/empty rendering) only run on the clone; dev stays read-only.
 * KD4_STAGE=recon,interact,consistency,motion,layout limits the run (default all).
 */
const fs = require('node:fs');
const path = require('node:path');

const MODEL = 'tp.kd.overview';
const NO_FILTER = { project_id: false, owner_id: false, date_from: false, date_to: false };
const STATES = ['draft', 'in_review', 'returned'];
const TASK_KEYS = ['done', 'overdue', 'open'];
const BID_KEYS = ['identified', 'preparation', 'submitted'];
const CRED_KEYS = ['expired', 'soon', 'later'];
const PCT = new Intl.NumberFormat('vi-VN', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const RATIO = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 });
const SOURCE_LEAF = {
  allocation: 'Giao khoán và thầu phụ', production: 'Sản lượng theo kỳ', acceptance: 'Hồ sơ nghiệm thu',
  payment: 'Đề nghị thanh toán', plan: 'Kế hoạch định kỳ', credential: 'Năng lực và chứng chỉ',
  obligation: 'Nghĩa vụ và hồ sơ còn thiếu',
};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const fmtDate = value => (value ? value.split('-').reverse().join('/') : '');
const isDash = url => new URL(url).pathname.endsWith('/tp.kd.overview/get_kd_dashboard');
const isRows = url => new URL(url).pathname.endsWith('/tp.kd.overview/get_kd_project_rows');

/** Everything the reviewer can read on the Overview, straight from the DOM (runs in the page). */
function readDom() {
  const q = (s, r = document) => r.querySelector(s);
  const qa = (s, r = document) => [...r.querySelectorAll(s)];
  const txt = el => (el?.textContent || '').replace(/\s+/g, ' ').trim();
  const num = el => (el ? Number(txt(el).replace(/\D/g, '')) : null);
  const ov = q('.o_tp_kd_ov');
  return {
    center: num(q('.o_tp_kd_d01 .o_tp_kd_donut_center b')),
    legend: Object.fromEntries(qa('.o_tp_kd_d01 .o_tp_kd_dleg').map(b => [b.dataset.state,
      { n: num(q('b', b)), pct: txt(q('small', b)), disabled: b.disabled }])),
    slices: qa('.o_tp_kd_d01 .o_tp_kd_slice').map(c => c.dataset.state),
    rows: qa('.o_tp_kd_g01 .o_tp_kd_bar_row').map(li => ({
      source: li.dataset.source, total: num(q('.o_tp_kd_bar_total', li)), label: !!q('button.o_tp_kd_bar_label', li),
      segs: Object.fromEntries(qa('.o_tp_kd_seg_btn', li).map(b => [b.dataset.state, num(q('span', b))])),
    })),
    d01Empty: txt(q('.o_tp_kd_d01 .o_tp_kd_empty')), d01NoAccess: !!q('.o_tp_kd_d01 .o_tp_kd_noaccess'),
    d01Hints: qa('.o_tp_kd_d01 .o_tp_kd_hint').map(txt),
    kpis: Object.fromEntries(qa('.o_tp_kd_kpi').map(b => [b.dataset.kpi,
      { n: num(q('.o_tp_kd_kpi_value', b)), note: txt(q('.o_tp_kd_kpi_note', b)), label: txt(q('.o_tp_kd_kpi_label', b)) }])),
    scale: Object.fromEntries(qa('.o_tp_kd_scale_btn').map(b => [b.dataset.key,
      { n: num(q('b', b)), hint: b.dataset.tooltip || '', described: txt(document.getElementById(b.getAttribute('aria-describedby'))) }])),
    taskLegend: qa('.o_tp_kd_tasks .o_tp_kd_legend li').map(li => num(q('b', li))),
    taskRows: qa('.o_tp_kd_tasks .o_tp_kd_bar_row').map(li => ({
      project: Number(li.dataset.project), total: num(q('.o_tp_kd_bar_total', li)),
      segs: Object.fromEntries(qa('.o_tp_kd_seg_btn', li).map(b => [b.dataset.bucket, num(q('span', b))])),
    })),
    taskRange: txt(q('.o_tp_kd_tasks .o_tp_kd_range')),
    taskHint: qa('.o_tp_kd_tasks .o_tp_kd_hint').map(txt).join(' '),
    taskNoAccess: !!q('.o_tp_kd_tasks .o_tp_kd_noaccess'),
    leadTotal: num(q('.o_tp_kd_leads .o_tp_kd_total_btn b')),
    leadBid: Object.fromEntries(qa('.o_tp_kd_leads [data-bid]').map(b => [b.dataset.bid, num(b)])),
    leadDirect: num(q('.o_tp_kd_leads [data-route="direct"]')),
    leadLabels: qa('.o_tp_kd_leads .o_tp_kd_bar_label').map(txt),
    leadNoAccess: !!q('.o_tp_kd_leads .o_tp_kd_noaccess'),
    primary: qa('.btn-primary', ov).length,
    listsBtn: q('.o_tp_kd_tb_lists')?.className || '',
    text: ov?.innerText || '',
  };
}

function readPlan() {
  const txt = el => (el?.textContent || '').replace(/\s+/g, ' ').trim();
  return [...document.querySelectorAll('.o_tp_kd_plan_row')].map(li => ({
    plan: Number(li.dataset.plan), unit: txt(li.querySelector('.o_tp_kd_plan_unit')),
    vals: [...li.querySelectorAll('.o_tp_kd_plan_val')].map(txt), pill: txt(li.querySelector('.o_tp_kd_pill')),
  }));
}

function readCred() {
  const txt = el => (el?.textContent || '').replace(/\s+/g, ' ').trim();
  return {
    center: Number(txt(document.querySelector('.o_tp_kd_cred .o_tp_kd_donut_center b')).replace(/\D/g, '')) || 0,
    legend: Object.fromEntries([...document.querySelectorAll('.o_tp_kd_cred .o_tp_kd_dleg')].map(b => [b.dataset.bucket,
      { n: Number(txt(b.querySelector('b')).replace(/\D/g, '')), label: txt(b.querySelector('.o_tp_kd_dleg_label')), disabled: b.disabled }])),
    soon: document.querySelectorAll('.o_tp_kd_cred_soon li').length,
    empty: txt(document.querySelector('#tp_kd_panel_detail .o_tp_kd_empty')),
  };
}

function layoutFacts() {
  const ov = document.querySelector('.o_tp_kd_ov');
  const r = s => document.querySelector(s)?.getBoundingClientRect();
  const se = document.scrollingElement;
  return {
    docOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    ovOverflow: ov ? ov.scrollWidth - ov.clientWidth : null,
    pageScroll: se.scrollHeight - se.clientHeight,
    ovRoom: ov ? ov.scrollHeight - ov.clientHeight : null,
    overflowY: ov ? getComputedStyle(ov).overflowY : null,
    head: r('.o_tp_kd_ov_head')?.bottom, filters: r('.o_tp_kd_filters')?.bottom, kpis: r('.o_tp_kd_kpis')?.bottom,
    d01: r('.o_tp_kd_d01'), g01: r('.o_tp_kd_g01'), pairBottom: r('.o_tp_kd_pair')?.bottom,
    kpiTops: [...document.querySelectorAll('.o_tp_kd_kpi')].map(k => Math.round(k.getBoundingClientRect().top)),
    innerHeight, innerWidth,
  };
}

module.exports = async function overview(ctx) {
  const { browser, login, watch, shot, shotFull, out, errors, target } = ctx;
  // The web client keeps background requests open (bus, service worker), so "network idle" is only a short hint.
  async function settle(p) {
    await p.waitForLoadState('networkidle', { timeout: 2500 }).catch(() => {});
    await p.waitForTimeout(300);
  }
  async function openOverview(p) {
    await p.goto(`${ctx.base}/odoo/action-tp_kd_workspace.action_overview`, { timeout: 90000 });
    await p.locator('.o_tp_kd_ov').first().waitFor({ timeout: 60000 });
  }
  // Payload text (money, dates) is formatted in the actor's language, exactly as the web client asks for it.
  const userContext = new WeakMap();
  async function ok(context, model, method, args, kwargs = {}) {
    if (!userContext.has(context)) {
      const info = await context.request.post(`${ctx.base}/web/session/get_session_info`, { data: { jsonrpc: '2.0', method: 'call', params: {} } });
      userContext.set(context, (await info.json()).result?.user_context || {});
    }
    return ctx.ok(context, model, method, args, { ...kwargs, context: { ...userContext.get(context), ...(kwargs.context || {}) } });
  }
  const mocks = target === 'clone';
  const stage = process.env.KD4_STAGE || 'all';
  const run = name => stage === 'all' || stage.split(',').includes(name);
  const evidence = { target, recon: {}, interact: {}, consistency: {}, motion: {}, layout: {}, retries: 0 };
  const failures = [];
  let lastPage = null;
  const check = (name, condition, detail) => {
    try { ctx.check(name, condition, detail); } catch (error) { failures.push(error.message.slice(0, 700)); }
  };
  async function section(name, body) {
    if (!run(name)) return;
    const started = Date.now();
    try {
      await body();
    } catch (error) {
      if (lastPage && !lastPage.isClosed()) {
        await shot(lastPage, `abort-${name}`).catch(() => {});
        evidence[`abort_${name}_url`] = lastPage.url();
      }
      failures.push(`[${name}] aborted: ${String(error.message || error).split('\n').slice(0, 4).join(' | ').slice(0, 700)}`);
    }
    evidence[`time_${name}`] = Math.round((Date.now() - started) / 1000);
  }
  async function ready(p) {
    await p.locator('.o_tp_kd_ov .o_tp_kd_data').first().waitFor({ timeout: 30000 });
    await p.waitForFunction(() => document.querySelector('.o_tp_kd_ov')?.getAttribute('aria-busy') === 'false', null, { timeout: 30000 });
    await settle(p);
  }
  /** Log in and open the Overview. One retry with a fresh session: a just-rotated session was once seen
   * answering "user is not connected" to the first get_views (recorded in evidence.retries). */
  async function open(key, { contextOptions = {}, init = null, quiet = false } = {}) {
    for (let attempt = 1; ; attempt++) {
      const context = await login(browser, key, contextOptions);
      if (init) await context.addInitScript(init);
      const p = await context.newPage();
      p.setDefaultTimeout(30000);
      const local = [];
      if (quiet) {
        // Mocked failures log expected network errors; page errors still fail the run.
        p.on('pageerror', error => errors.push(`pageerror ${error.message}`));
        p.on('console', msg => { if (msg.type() === 'error') local.push(msg.text().slice(0, 200)); });
      } else {
        watch(p);
      }
      try {
        await openOverview(p);
        await ready(p);
        lastPage = p;
        return { context, p, local };
      } catch (error) {
        await context.close();
        if (attempt >= 2) throw error;
        evidence.retries += 1;
      }
    }
  }
  async function drillCount(context, key, filters, params) {
    const action = await ok(context, MODEL, 'action_kd_open', [key, filters, params]);
    return ok(context, action.res_model, 'search_count', [action.domain || []], { context: action.context || {} });
  }
  async function listCount(p) {
    await p.locator('.o_action_manager .o_list_view').first().waitFor({ timeout: 30000 });
    await settle(p);
    return p.evaluate(() => {
      const limit = document.querySelector('.o_pager_limit');
      return {
        n: limit ? Number(limit.textContent.replace(/\D/g, '')) : document.querySelectorAll('.o_list_view .o_data_row').length,
        active: document.querySelector('.o_tp_kd_sb_leaf[aria-current="page"]')?.innerText.trim() || null,
      };
    });
  }
  /** Back to the Overview: through the breadcrumb as a user does, or with the browser Back button once the web
   * client has written the new URL (Back pressed before that push lands on an older history entry). */
  async function back(p, how = 'crumb') {
    const crumb = p.locator('.o_breadcrumb .breadcrumb-item a').first();
    if (how === 'browser') {
      await p.waitForTimeout(800);
      await p.goBack();
    } else {
      await crumb.waitFor({ timeout: 10000 });
      await crumb.click();
    }
    await ready(p);
  }
  async function showDetail(p, tab) {
    await p.locator(`#tp_kd_tab_${tab}`).click();
    await p.waitForFunction(t => {
      const pane = document.querySelector('#tp_kd_panel_detail');
      return pane && !pane.classList.contains('is-busy') && !/Đang tải/.test(pane.innerText)
        && document.querySelector(`#tp_kd_tab_${t}`)?.getAttribute('aria-selected') === 'true';
    }, tab, { timeout: 30000 });
    await settle(p);
  }

  // ------------------------------------------------------------ A. numbers vs payload vs drill-down
  await section('recon', async () => {
    for (const key of ['reviewer', 'planner', 'editor', 'metadata']) {
      let opened;
      try {
        opened = await open(key);
      } catch (error) {
        failures.push(`[recon ${key}] could not open: ${String(error.message).slice(0, 200)}`);
        continue;
      }
      const { context, p } = opened;
      const d = await ok(context, MODEL, 'get_kd_dashboard', [NO_FILTER]);
      const dom = await p.evaluate(readDom);
      const ev = { totals: d.g01.totals, kpis: { ...d.kpis, breakdown: undefined }, g02: d.g02.totals, g03: d.g03, drill: {} };
      const t = d.g01.totals;
      const rowsSum = s => d.g01.rows.reduce((sum, r) => sum + r[s], 0);
      const blocked = d.g01.rows.filter(r => !r.available).length;
      // A1/A2/A4/A6 donut + legend + bars
      if (blocked === d.g01.rows.length) {
        check(`A5 ${key} no permission shows the no-access message`, dom.d01NoAccess && dom.center === null, dom.d01Empty);
      } else if (!t.total) {
        check(`A5 ${key} empty state (not no-access)`, !dom.d01NoAccess && /Chưa có hồ sơ/.test(dom.d01Empty), dom.d01Empty);
      } else {
        check(`A1 ${key} centre = totals.total = Σ rows`, dom.center === t.total && t.total === rowsSum('total'), [dom.center, t.total]);
        for (const s of STATES) {
          const segSum = dom.rows.reduce((sum, r) => sum + (r.segs[s] || 0), 0);
          check(`A2 ${key} ${s}: legend = totals = Σ D02`, dom.legend[s]?.n === t[s] && segSum === t[s] && rowsSum(s) === t[s],
            [dom.legend[s], t[s], segSum]);
          check(`A4 ${key} ${s} percent`, dom.legend[s]?.pct === `${PCT.format((t[s] * 100) / t.total)}%`, [dom.legend[s]?.pct]);
          check(`B4 ${key} ${s} zero legend not clickable`, dom.legend[s]?.disabled === (t[s] === 0));
        }
        check(`A2 ${key} donut slices only for non-zero states`,
          JSON.stringify(dom.slices) === JSON.stringify(STATES.filter(s => t[s] > 0)), dom.slices);
        check(`A1 ${key} D02 rows in payload order`,
          JSON.stringify(dom.rows.map(r => r.source)) === JSON.stringify(d.g01.rows.map(r => r.source)), dom.rows.map(r => r.source));
        if (blocked) check(`A5 ${key} partial access note`, dom.d01Hints.some(h => h.startsWith(`${blocked} nhóm không có quyền xem`)), dom.d01Hints);
        for (const row of d.g01.rows) {
          const shown = dom.rows.find(r => r.source === row.source);
          check(`B4 ${key} ${row.source} zero segments have no button`,
            JSON.stringify(Object.keys(shown?.segs || {})) === JSON.stringify(STATES.filter(s => row[s] > 0)), shown?.segs);
          check(`A2 ${key} ${row.source} row total`, shown?.total === row.total, [shown?.total, row.total]);
          if (!row.available) continue;
          for (const s of STATES.filter(st => row[st] > 0)) {
            const n = await drillCount(context, 'g01', NO_FILTER, { source: row.source, state: s });
            ev.drill[`${row.source}.${s}`] = [row[s], n];
            check(`A3 ${key} ${row.source}.${s} segment = drill-down search_count`, shown.segs[s] === row[s] && n === row[s], [shown.segs[s], row[s], n]);
          }
        }
      }
      // A7 KPIs, A8 scale strip
      for (const k of ['review', 'returned', 'overdue', 'due']) {
        check(`A7 ${key} KPI ${k}`, dom.kpis[k]?.n === d.kpis[k], [dom.kpis[k]?.n, d.kpis[k]]);
      }
      const w = d.kpis.due_window;
      check(`A7 ${key} due window label`, dom.kpis.due?.label === 'Đến hạn trong 3 ngày'
        && dom.kpis.due.note.includes(`${fmtDate(w.from)} – ${fmtDate(w.to)}`) && dom.kpis.overdue.note.includes(fmtDate(d.today)), dom.kpis.due);
      for (const k of ['projects', 'contracts', 'revisions']) {
        check(`A8 ${key} scale ${k}`, dom.scale[k]?.n === d.kpis[k] && dom.scale[k].hint && dom.scale[k].hint === dom.scale[k].described,
          [dom.scale[k], d.kpis[k]]);
      }
      check(`A8 ${key} scale hints state their date/owner rule`, /không áp ngày/.test(dom.scale.projects?.hint)
        && /người tạo hợp đồng/.test(dom.scale.contracts?.hint) && /không áp bộ lọc ngày/.test(dom.scale.contracts?.hint)
        && /ngày ghi nhận/.test(dom.scale.revisions?.hint) && /không áp người phụ trách/.test(dom.scale.revisions?.hint));
      // A9 tasks
      if (!d.g02.available) {
        check(`A9 ${key} tasks no-access message`, dom.taskNoAccess);
      } else if (d.g02.rows.length) {
        check(`A9 ${key} task legend = g02.totals`, JSON.stringify(dom.taskLegend) === JSON.stringify(TASK_KEYS.map(k => d.g02.totals[k])), dom.taskLegend);
        check(`A9 ${key} task buckets add up`, TASK_KEYS.reduce((s, k) => s + d.g02.totals[k], 0) === d.g02.totals.total);
        const shownN = Math.min(8, d.g02.rows.length);
        check(`A9 ${key} task top N label`, dom.taskRows.length === shownN && dom.taskRange === `Đang xem ${shownN}/${d.g02.rows.length} dự án`, dom.taskRange);
        dom.taskRows.forEach((r, i) => {
          const row = d.g02.rows[i];
          check(`A9 ${key} task row ${row.code}`, r.project === row.project_id && r.total === row.total
            && TASK_KEYS.every(k => (r.segs[k] || 0) === row[k]), [r, row]);
        });
        if (d.g02.no_deadline) check(`A9 ${key} no-deadline note`, dom.taskHint.includes(`có ${d.g02.no_deadline} việc chưa có hạn`), dom.taskHint);
        const first = d.g02.rows[0];
        for (const k of TASK_KEYS.filter(b => first[b] > 0)) {
          const n = await drillCount(context, 'task', NO_FILTER, { bucket: k, project_id: first.project_id });
          ev.drill[`task.${first.code}.${k}`] = [first[k], n];
          check(`A9 ${key} task ${first.code}.${k} = drill-down`, n === first[k], [first[k], n]);
        }
      }
      // A10 opportunities
      if (!d.g03.available) {
        check(`A10 ${key} leads no-access message`, dom.leadNoAccess);
      } else if (d.g03.total) {
        check(`A10 ${key} lead total`, dom.leadTotal === d.g03.total && d.g03.total === BID_KEYS.reduce((s, b) => s + d.g03.bid[b], 0) + d.g03.direct);
        check(`A10 ${key} bid states + direct`, BID_KEYS.every(b => (dom.leadBid[b] || 0) === d.g03.bid[b]) && (dom.leadDirect || 0) === d.g03.direct,
          [dom.leadBid, dom.leadDirect]);
        check(`A10 ${key} submitted labelled unverified`, dom.leadLabels.includes('Đã khai báo nộp — chưa xác minh'), dom.leadLabels);
        for (const b of BID_KEYS.filter(s => d.g03.bid[s] > 0)) {
          const n = await drillCount(context, 'lead', NO_FILTER, { route: 'bid', bid_state: b });
          check(`A10 ${key} bid ${b} = drill-down`, n === d.g03.bid[b], [d.g03.bid[b], n]);
        }
        if (d.g03.direct) {
          const n = await drillCount(context, 'lead', NO_FILTER, { route: 'direct' });
          check(`A10 ${key} direct = drill-down`, n === d.g03.direct, [d.g03.direct, n]);
        }
      }
      // A11 plan (default tab, month)
      const plan = await ok(context, MODEL, 'get_kd_plan_compare', [NO_FILTER, 'month']);
      await p.waitForFunction(() => !/Đang tải/.test(document.querySelector('#tp_kd_panel_detail')?.innerText || 'Đang tải'), null, { timeout: 30000 });
      const planDom = await p.evaluate(readPlan);
      ev.plan = { rows: plan.rows.length, in_scope: plan.in_scope, excluded: plan.excluded };
      if (plan.available) {
        check(`A11 ${key} plan rows`, JSON.stringify(planDom.map(r => r.plan)) === JSON.stringify(plan.rows.map(r => r.plan_id)), planDom.map(r => r.plan));
        plan.rows.forEach((row, i) => {
          const r = planDom[i] || { vals: [], unit: '', pill: '' };
          const target = row.target_text || (row.target_state === 'unconfirmed' ? 'Mục tiêu chưa xác nhận' : 'Chưa có mục tiêu');
          const unit = row.currency || row.basis_label ? [row.currency, row.basis_label].filter(Boolean).join(' · ') : 'Chưa có dòng mục tiêu';
          const norm = v => (v || '').replace(/\s+/g, ' ').trim(); // money text carries a no-break space before ₫
          check(`A11 ${key} plan ${row.code} values/unit`, r.vals[0] === norm(target) && r.vals[1] === norm(row.source_text || row.status_label)
            && r.unit === norm(unit), [r, row]);
          check(`A11 ${key} plan ${row.code} unconfirmed never 0`, row.target_text || !/^0(\s|$)|^0\s?₫/.test(r.vals[0]), r.vals);
          check(`A11 ${key} plan ${row.code} pill`, r.pill === (row.ratio !== null ? `${RATIO.format(row.ratio)}%` : 'Chưa so sánh'), [r.pill, row.ratio]);
        });
        check(`A11 ${key} plan never adds periods or money`, !/Tổng/.test(await p.locator('#tp_kd_panel_detail').innerText()));
      }
      // A12 credentials (lazy tab)
      await showDetail(p, 'cred');
      const cred = await ok(context, MODEL, 'get_kd_credential_expiry', [NO_FILTER]);
      const credDom = await p.evaluate(readCred);
      ev.cred = cred.buckets;
      if (cred.available && CRED_KEYS.some(b => cred.buckets[b])) {
        check(`A12 ${key} cred buckets`, CRED_KEYS.every(b => credDom.legend[b]?.n === cred.buckets[b])
          && credDom.center === CRED_KEYS.reduce((s, b) => s + cred.buckets[b], 0), [credDom, cred.buckets]);
        check(`A12 ${key} cred bounds in labels`, credDom.legend.expired?.label.includes(fmtDate(cred.bounds.today))
          && credDom.legend.soon?.label.includes(fmtDate(cred.bounds.soon_until)) && credDom.legend.later?.label.includes(fmtDate(cred.bounds.soon_until)),
          credDom.legend);
        for (const b of CRED_KEYS.filter(k => cred.buckets[k] > 0)) {
          const n = await drillCount(context, 'credential', NO_FILTER, { bucket: b });
          check(`A12 ${key} cred ${b} = drill-down`, n === cred.buckets[b], [cred.buckets[b], n]);
        }
      }
      // D8 + one primary action + "Xem dữ liệu" stays a menu
      check(`D8 ${key} no G0x/D0x codes on screen`, !/\b[GD]0\d\b/.test(dom.text), (dom.text.match(/\b[GD]0\d\b/g) || []).slice(0, 3));
      check(`B ${key} at most one primary button`, dom.primary <= 1, dom.primary);
      check(`B ${key} Xem dữ liệu is a secondary menu`, /btn-secondary/.test(dom.listsBtn) && !/btn-primary/.test(dom.listsBtn));
      if (key === 'reviewer') {
        // A8 filter semantics behind the tooltips (server answers, same actor).
        const owner = d.options.owners[0]?.id;
        if (owner) {
          const byOwner = await ok(context, MODEL, 'get_kd_dashboard', [{ ...NO_FILTER, owner_id: owner }]);
          check('A8 owner filter leaves projects/revisions', byOwner.kpis.projects === d.kpis.projects && byOwner.kpis.revisions === d.kpis.revisions);
        }
        const far = await ok(context, MODEL, 'get_kd_dashboard', [{ ...NO_FILTER, date_from: '2099-01-01' }]);
        check('A8 date filter leaves projects/contracts', far.kpis.projects === d.kpis.projects && far.kpis.contracts === d.kpis.contracts);
        // A5 empty state from a real filter (no record has a 2099 date).
        await p.locator('.o_tp_kd_filters input[type="date"]').first().fill('2099-01-01');
        await p.locator('.o_tp_kd_filters input[type="date"]').first().dispatchEvent('change');
        await ready(p);
        const empty = await p.evaluate(readDom);
        check('A5 empty filter shows the empty state, not no-access', far.g01.totals.total !== 0
          || (/Chưa có hồ sơ/.test(empty.d01Empty) && !empty.d01NoAccess && empty.center === 0), [far.g01.totals, empty.d01Empty]);
        await shot(p, 'after-empty-filter-1440');
        await p.locator('.o_tp_kd_tb_clear').click();
        await ready(p);
      }
      evidence.recon[key] = ev;
      await context.close();
    }
  });

  // ------------------------------------------------------------ B. interaction and drill-down
  await section('interact', async () => {
    const { context, p } = await open('reviewer');
    const d = await ok(context, MODEL, 'get_kd_dashboard', [NO_FILTER]);
    const t = d.g01.totals;
    const calls = [];
    p.on('request', r => { if (r.url().includes('/web/dataset/call_kw/')) calls.push(r.url()); });
    const opacity = s => p.evaluate(sel => [...document.querySelectorAll(sel)].map(e => Number(getComputedStyle(e).opacity)), s);
    if (t.total) {
      // B1 hover/focus highlight with no RPC
      calls.length = 0;
      const live = STATES.filter(s => t[s] > 0);
      for (const s of live) {
        await p.locator(`.o_tp_kd_d01 .o_tp_kd_dleg[data-state="${s}"]`).hover();
        await p.waitForTimeout(250);
        const other = live.find(x => x !== s);
        if (other) {
          const dim = await opacity(`.o_tp_kd_g01 .o_tp_kd_seg_btn[data-state="${other}"]`);
          const on = await opacity(`.o_tp_kd_g01 .o_tp_kd_seg_btn[data-state="${s}"]`);
          check(`B1 hover ${s} highlights D02`, dim.every(o => o < 0.5) && on.every(o => o > 0.95), [dim.slice(0, 2), on.slice(0, 2)]);
        }
      }
      await p.locator('.o_tp_kd_g01 .o_tp_kd_seg_btn').first().hover();
      await p.waitForTimeout(200);
      if (live.length > 1) await shot(p, 'after-hover-1440');
      await p.mouse.move(5, 5);
      check('B1 hover sends no RPC', calls.length === 0, calls.slice(0, 3));
      // B3 keyboard: Tab to the next legend item (focus-visible highlight), Enter selects
      await p.locator('.o_tp_kd_d01 .o_tp_kd_dleg:not([disabled])').first().focus();
      await p.keyboard.press('Tab');
      const focused = await p.evaluate(() => document.activeElement?.dataset?.state || document.activeElement?.className);
      const sel = live.includes(focused) ? focused : live[0];
      if (live.includes(focused)) {
        await p.keyboard.press('Enter');
      } else {
        await p.locator(`.o_tp_kd_d01 .o_tp_kd_dleg[data-state="${sel}"]`).click();
      }
      await p.waitForTimeout(300);
      const picked = await p.evaluate(() => ({
        sel: document.querySelector('.o_tp_kd_pair')?.dataset.sel,
        pressed: document.querySelector('.o_tp_kd_dleg[aria-pressed="true"]')?.dataset.state,
        head: document.querySelector('.o_tp_kd_pick_head p')?.textContent.replace(/\s+/g, ' ').trim(),
        btns: [...document.querySelectorAll('.o_tp_kd_pick_list li')].map(li => ({ source: li.dataset.source,
          n: li.querySelector('.o_tp_kd_pick_btn b')?.textContent || null, off: !!li.querySelector('.o_tp_kd_pick_off') })),
        center: Number(document.querySelector('.o_tp_kd_d01 .o_tp_kd_donut_center b')?.textContent),
      }));
      evidence.interact.select = picked;
      check('B2 select keeps the denominator', picked.sel === sel && picked.pressed === sel && picked.center === t.total
        && picked.head?.includes(`${t[sel]} · ${PCT.format((t[sel] * 100) / t.total)}%`) && picked.head.includes(`trên ${t.total} hồ sơ`), picked);
      check('B2 source chooser = rows with that state', d.g01.rows.every(row => {
        const b = picked.btns.find(x => x.source === row.source);
        return b && (row.available && row[sel] ? Number(b.n) === row[sel] : b.off);
      }), picked.btns);
      check('B2 selecting sends no RPC', calls.length === 0, calls.slice(0, 3));
      await shot(p, 'after-select-1440');
      // B3 Esc clears; slice click selects; "Bỏ chọn" clears; legend toggles
      await p.keyboard.press('Escape');
      await p.waitForTimeout(200);
      check('B3 Esc clears the selection', !(await p.locator('.o_tp_kd_pair').getAttribute('data-sel')) && await p.locator('.o_tp_kd_pick').count() === 0);
      await p.locator(`.o_tp_kd_d01 .o_tp_kd_slice[data-state="${sel}"]`).dispatchEvent('click');
      await p.waitForTimeout(200);
      check('B2 donut slice selects', (await p.locator('.o_tp_kd_pair').getAttribute('data-sel')) === sel);
      await p.locator('.o_tp_kd_pick_clear').click();
      await p.waitForTimeout(200);
      check('B3 Bỏ chọn clears', await p.locator('.o_tp_kd_pick').count() === 0);
      // B2 pick → list (right model + state + filters), sidebar leaf, Back
      await p.locator(`.o_tp_kd_d01 .o_tp_kd_dleg[data-state="${sel}"]`).click();
      const pickRow = d.g01.rows.find(r => r.available && r[sel] > 0);
      await p.locator(`.o_tp_kd_pick_list li[data-source="${pickRow.source}"] .o_tp_kd_pick_btn`).click();
      const viaPick = await listCount(p);
      check('B2 source button opens that list', viaPick.n === pickRow[sel] && viaPick.active?.includes(SOURCE_LEAF[pickRow.source]), [viaPick, pickRow[sel]]);
      await back(p, 'browser');
      // B4 D02 segment → list directly
      const segRow = d.g01.rows.find(r => r.available && r.total > 0);
      const segState = STATES.find(s => segRow[s] > 0);
      await p.locator(`.o_tp_kd_g01 .o_tp_kd_bar_row[data-source="${segRow.source}"] .o_tp_kd_seg_btn[data-state="${segState}"]`).click();
      const viaSeg = await listCount(p);
      check('B4 D02 segment opens the list', viaSeg.n === segRow[segState] && viaSeg.active?.includes(SOURCE_LEAF[segRow.source]), [viaSeg, segRow[segState]]);
      await back(p);
      check('B4 Back returns to Tổng quan', (await p.locator('.o_tp_kd_sb_leaf[aria-current="page"]').innerText()).includes('Tổng quan'));
    }
    // B5 tasks / leads / credentials / plan open the right group
    const task = d.g02.rows[0];
    const taskKey = task && TASK_KEYS.find(k => task[k] > 0);
    if (taskKey) {
      await p.locator(`.o_tp_kd_tasks .o_tp_kd_bar_row[data-project="${task.project_id}"] .o_tp_kd_seg_btn[data-bucket="${taskKey}"]`).click();
      const n = await listCount(p);
      check('B5 task segment opens that group', n.n === task[taskKey], [n, task[taskKey]]);
      await back(p);
    }
    const bid = BID_KEYS.find(b => d.g03.bid[b] > 0);
    if (bid) {
      await p.locator(`.o_tp_kd_leads [data-bid="${bid}"]`).click();
      const n = await listCount(p);
      check('B5 bid segment opens that group', n.n === d.g03.bid[bid] && n.active?.includes('Cơ hội và hồ sơ thầu'), [n, d.g03.bid[bid]]);
      await back(p);
    }
    await showDetail(p, 'plan');
    await shot(p, 'after-plan-1440');
    if (await p.locator('.o_tp_kd_plan_name').count()) {
      await p.locator('.o_tp_kd_plan_name').first().click();
      await p.locator('.o_action_manager .o_form_view').first().waitFor({ timeout: 30000 });
      check('B5 plan row opens the plan form', true);
      await back(p);
    }
    await showDetail(p, 'cred');
    await p.locator('.o_tp_kd_detail').scrollIntoViewIfNeeded();
    await shot(p, 'after-cred-1440');
    const cred = await ok(context, MODEL, 'get_kd_credential_expiry', [NO_FILTER]);
    const bucket = CRED_KEYS.find(b => cred.buckets[b] > 0);
    if (bucket) {
      await p.locator(`.o_tp_kd_cred .o_tp_kd_dleg[data-bucket="${bucket}"]`).click();
      const n = await listCount(p);
      check('B5 credential bucket opens that group', n.n === cred.buckets[bucket], [n, cred.buckets[bucket]]);
      await back(p);
    }
    // Tab keyboard (roving): End/Home
    await p.locator('#tp_kd_tab_plan').click();
    await p.locator('#tp_kd_tab_plan').press('End');
    await p.waitForTimeout(300);
    const tabs = await p.evaluate(() => ({ cred: document.querySelector('#tp_kd_tab_cred')?.getAttribute('aria-selected'),
      focus: document.activeElement?.id }));
    check('B3 detail tabs keyboard (End)', tabs.cred === 'true' && tabs.focus === 'tp_kd_tab_cred', tabs);
    await p.keyboard.press('Home');
    await p.waitForTimeout(300);
    check('B3 detail tabs keyboard (Home)', await p.locator('#tp_kd_tab_plan').getAttribute('aria-selected') === 'true');
    // B6 project table: pager, column chooser (sort/row menu are in the KD-UI-003 regression)
    const rows = await ok(context, MODEL, 'get_kd_project_rows', [NO_FILTER, '', 'code asc', 0, 10]);
    const range = (await p.locator('.o_tp_kd_projects .o_tp_kd_pager').first().innerText().catch(() => '')).replace(/\s+/g, ' ');
    check('B6 project pager matches the server total', range.includes(`/ ${rows.total}`), [range, rows.total]);
    // B7 KPI → Việc của tôi tab + scroll
    await p.locator('.o_tp_kd_kpi[data-kpi="returned"]').click();
    await p.waitForTimeout(900);
    const mine = await p.evaluate(() => {
      const r = document.getElementById('tp_kd_mine').getBoundingClientRect();
      return { top: r.top, h: innerHeight, tab: document.querySelector('#tp_kd_mtab_returned')?.getAttribute('aria-selected') };
    });
    check('B7 KPI click opens its tab and scrolls to Việc của tôi', mine.tab === 'true' && mine.top >= 0 && mine.top < mine.h, mine);
    // B8 source table on demand
    const src = await ok(context, MODEL, 'get_kd_source_table', [NO_FILTER]);
    await p.locator('.o_tp_kd_sources .o_tp_kd_disclosure').click();
    await p.locator('#tp_kd_sources_body table').waitFor({ timeout: 30000 });
    const srcDom = await p.evaluate(() => [...document.querySelectorAll('#tp_kd_sources_body tbody tr')]
      .map(tr => [...tr.querySelectorAll('td')].map(td => Number(td.textContent.replace(/\D/g, '')))));
    check('B8 source table numbers match', src.rows.every((r, i) => JSON.stringify(srcDom[i]) === JSON.stringify(['all', 'review', 'returned', 'overdue', 'due'].map(q => r[q]))),
      srcDom.slice(0, 2));
    evidence.interact.calls = calls.length;
    await context.close();
  });

  // ------------------------------------------------------------ C. consistency (clone: mocks)
  await section('consistency', async () => {
    if (!mocks) return;
    const { context, p, local } = await open('reviewer', { quiet: true });
    const d = await ok(context, MODEL, 'get_kd_dashboard', [NO_FILTER]);
    const projectId = d.options.projects.find(o => o.id)?.id;
    const read = () => p.evaluate(readDom);
    // C1 late answer of an older filter
    let n1 = 0;
    await p.route(url => isDash(url), async route => {
      if (n1++ === 0) {
        const response = await route.fetch();
        await sleep(2500);
        await route.fulfill({ response });
      } else {
        await route.continue();
      }
    });
    await p.locator('.o_tp_kd_filters select').first().selectOption(String(projectId));
    await p.waitForTimeout(200);
    await p.locator('.o_tp_kd_tb_clear').click();
    await p.waitForTimeout(3300);
    await ready(p);
    let now = await read();
    check('C1 newest filter wins over a late answer', now.scale.projects?.n === d.kpis.projects && now.center === d.g01.totals.total
      && await p.locator('.o_tp_kd_filters select').first().inputValue() === '', [now.scale.projects, now.center]);
    await p.unrouteAll({ behavior: 'wait' });
    // C2 partial (sort) in flight while a full refresh starts: no stuck busy/loading
    let n2 = 0;
    await p.route(url => isRows(url), async route => {
      if (n2++ === 0) {
        const response = await route.fetch();
        await sleep(2000);
        await route.fulfill({ response });
      } else {
        await route.continue();
      }
    });
    await p.locator('.o_tp_kd_projects thead th button').first().click();
    await p.waitForTimeout(150);
    await p.locator('.o_tp_kd_tb_refresh').click();
    await p.waitForTimeout(2600);
    await ready(p);
    const stuck = await p.evaluate(() => ({
      busy: document.querySelectorAll('.o_tp_kd_ov .is-busy').length,
      loading: document.querySelector('.o_tp_kd_ov').classList.contains('is-loading'),
      sort: document.querySelector('.o_tp_kd_projects thead th[aria-sort]')?.getAttribute('aria-sort'),
      first: document.querySelector('.o_tp_kd_projects .o_tp_kd_proj_name')?.textContent.replace(/\s+/g, ' ').trim(),
    }));
    const desc = await ok(context, MODEL, 'get_kd_project_rows', [NO_FILTER, '', 'code desc', 0, 10]);
    check('C2 partial during main load does not stick', stuck.busy === 0 && !stuck.loading && stuck.sort === 'descending'
      && stuck.first?.includes(desc.rows[0]?.code), [stuck, desc.rows[0]?.code]);
    await p.unrouteAll({ behavior: 'wait' });
    // C3 network failure keeps the data, marks it stale, keeps the old time
    now = await read();
    const stamp = (await p.locator('.o_tp_kd_stamp').innerText()).trim();
    let n3 = 0;
    await p.route(url => isDash(url), route => (n3++ === 0 ? route.abort('failed') : route.continue()));
    await p.locator('.o_tp_kd_tb_refresh').click();
    await p.locator('.o_tp_kd_stamp.is-stale').waitFor({ timeout: 15000 });
    const stale = await read();
    const staleStamp = (await p.locator('.o_tp_kd_stamp').innerText()).trim();
    check('C3 failed refresh keeps data + old time, marked stale', stale.center === now.center && stale.kpis.review?.n === now.kpis.review?.n
      && staleStamp.startsWith(stamp) && /chưa làm mới được/.test(staleStamp)
      && /Chưa làm mới được/.test(await p.locator('.o_tp_kd_alert').innerText()), [stamp, staleStamp]);
    await shot(p, 'after-stale-1440');
    await p.locator('.o_tp_kd_alert .btn-link').click();
    await ready(p);
    check('C3 retry clears stale', await p.locator('.o_tp_kd_stamp.is-stale').count() === 0 && await p.locator('.o_tp_kd_alert').count() === 0);
    await p.unrouteAll({ behavior: 'wait' });
    // C4 access error wipes every number
    await p.route(url => isDash(url), async route => {
      const body = route.request().postDataJSON();
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        jsonrpc: '2.0', id: body?.id ?? null,
        error: { code: 200, message: 'Odoo Server Error', data: { name: 'odoo.exceptions.AccessError',
          message: 'Bạn không có quyền xem dữ liệu này (mô phỏng kiểm thử).', arguments: [], context: {}, debug: '' } },
      }) });
    });
    await p.locator('.o_tp_kd_tb_refresh').click();
    await p.locator('.o_tp_kd_denied').waitFor({ timeout: 15000 });
    await p.waitForTimeout(400);
    const wiped = await p.evaluate(() => {
      const ov = document.querySelector('.o_tp_kd_ov');
      return { data: !!ov.querySelector('.o_tp_kd_data'), scale: !!ov.querySelector('.o_tp_kd_scale'), filters: !!ov.querySelector('.o_tp_kd_filters'),
        stamp: !!ov.querySelector('.o_tp_kd_stamp'), tables: ov.querySelectorAll('table').length, digits: /\d/.test(ov.innerText),
        dialogs: document.querySelectorAll('.o_error_dialog, .o_dialog .modal-content').length };
    });
    check('C4 access error wipes data, only the message stays', !wiped.data && !wiped.scale && !wiped.filters && !wiped.stamp
      && wiped.tables === 0 && !wiped.digits && wiped.dialogs === 0, wiped);
    await shot(p, 'after-denied-1440');
    await p.unrouteAll({ behavior: 'wait' });
    await p.locator('.o_tp_kd_denied .btn').click();
    await ready(p);
    check('C4 retry after access restored', (await read()).center === d.g01.totals.total);
    // A5 rendering: no permission vs partial vs empty (client mocks of the same payload shape)
    const mock = async (mutate, name) => {
      await p.route(url => isDash(url), async route => {
        const response = await route.fetch();
        const json = await response.json();
        mutate(json.result);
        await route.fulfill({ response, json });
      });
      await p.locator('.o_tp_kd_tb_refresh').click();
      await p.waitForTimeout(300);
      await ready(p);
      const dom = await read();
      await shot(p, name);
      await p.unrouteAll({ behavior: 'wait' });
      return dom;
    };
    const zero = r => { for (const s of [...STATES, 'total']) r[s] = 0; };
    const retotal = g => { g.totals = Object.fromEntries([...STATES, 'total'].map(s => [s, g.rows.reduce((a, r) => a + r[s], 0)])); };
    const none = await mock(res => { res.g01.rows.forEach(r => { r.available = false; zero(r); }); retotal(res.g01); }, 'after-mock-noaccess-1440');
    check('A5 no permission ≠ empty', none.d01NoAccess && /quyền/.test(none.d01Empty) && none.center === null, none.d01Empty);
    const part = await mock(res => { res.g01.rows[0].available = false; zero(res.g01.rows[0]); retotal(res.g01); }, 'after-mock-partial-1440');
    check('A5 partial permission note', part.d01Hints.some(h => h.startsWith('1 nhóm không có quyền xem')) && !part.rows[0].label, part.d01Hints);
    const empty = await mock(res => { res.g01.rows.forEach(zero); retotal(res.g01); }, 'after-mock-empty-1440');
    check('A5 empty ≠ no permission', !empty.d01NoAccess && /Chưa có hồ sơ/.test(empty.d01Empty), empty.d01Empty);
    await p.locator('.o_tp_kd_tb_refresh').click();
    await ready(p);
    evidence.consistency.console = local.slice(0, 10);
    await context.close();
  });

  // ------------------------------------------------------------ D. motion
  const introProbe = () => {
    window.__kdIntro = { seen: false, anims: [] };
    const watchIntro = () => {
      const on = document.querySelector('.o_tp_kd_ov.is-intro');
      const probe = window.__kdIntro;
      if (on && !probe.seen) {
        probe.seen = true;
        probe.at = performance.now();
        requestAnimationFrame(() => {
          probe.anims = document.getAnimations().filter(a => a.effect?.target?.closest?.('.o_tp_kd_ov'))
            .map(a => ({ name: a.animationName, duration: a.effect.getTiming().duration, delay: a.effect.getTiming().delay }));
        });
      }
      if (probe.seen && !probe.end && !on) probe.end = performance.now();
    };
    new MutationObserver(watchIntro).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  };
  const kdAnims = p => p.evaluate(() => document.getAnimations().filter(a => a.effect?.target?.closest?.('.o_tp_kd_ov'))
    .map(a => a.animationName).filter(n => /sweep|grow/.test(n)));
  await section('motion', async () => {
    {
      const { context, p } = await open('reviewer', { init: introProbe });
      await p.waitForTimeout(1500);
      const probe = await p.evaluate(() => window.__kdIntro);
      evidence.motion.intro = probe;
      const sweep = probe.anims.filter(a => a.name === 'tp-kd-ov-sweep');
      const grow = probe.anims.filter(a => a.name === 'tp-kd-ov-grow');
      check('D1 donut draws once ≈700ms', probe.seen && sweep.length === 1 && sweep[0].duration >= 600 && sweep[0].duration <= 750, sweep);
      check('D1 bars grow < 800ms total', grow.length > 0 && grow.every(a => a.duration >= 400 && a.duration <= 550)
        && Math.max(...grow.map(a => a.delay + a.duration)) < 800, grow.map(a => a.delay + a.duration));
      check('D1 other transitions ≤ 250ms', probe.anims.filter(a => !/sweep|grow/.test(a.name)).every(a => a.duration <= 250), probe.anims);
      check('D1 intro class removed', probe.end && probe.end - probe.at < 1500, [probe.at, probe.end]);
      // no replay on sort / hover / select
      await p.locator('.o_tp_kd_projects thead th button').first().click();
      await p.locator('.o_tp_kd_d01 .o_tp_kd_dleg:not([disabled])').first().hover();
      await p.locator('.o_tp_kd_d01 .o_tp_kd_dleg:not([disabled])').first().click();
      await p.waitForTimeout(400);
      check('D1 no replay on sort/hover/select', await p.locator('.o_tp_kd_ov.is-intro').count() === 0 && (await kdAnims(p)).length === 0);
      // D2 preference "Giảm chuyển động" (local to this browser) + reload
      await p.locator('.o_tp_kd_tb_prefs').click();
      await p.getByRole('radio', { name: 'Giảm chuyển động' }).first().click();
      await p.keyboard.press('Escape');
      await p.reload();
      await ready(p);
      const reducedPref = await p.evaluate(() => ({ seen: window.__kdIntro.seen, cls: document.querySelector('.o_tp_kd_ov').classList.contains('is-reduced') }));
      check('D2 reduced preference: no intro', reducedPref.cls && !reducedPref.seen && (await kdAnims(p)).length === 0, reducedPref);
      await context.close();
    }
    {
      const { context, p } = await open('reviewer', { init: introProbe, contextOptions: { reducedMotion: 'reduce' } });
      await p.waitForTimeout(800);
      const os = await p.evaluate(() => ({ seen: window.__kdIntro.seen,
        tr: getComputedStyle(document.querySelector('.o_tp_kd_g01 .o_tp_kd_seg_btn') || document.body).transitionDuration }));
      check('D2 OS reduced motion: no intro/transition', !os.seen && (await kdAnims(p)).length === 0 && /^0s/.test(os.tr), os);
      await context.close();
    }
    {
      // D3 enter/leave repeatedly: one Overview root, no page errors
      const before = errors.length;
      const { context, p } = await open('reviewer');
      for (let i = 0; i < 5; i++) {
        await p.locator('.o_tp_kd_sb_leaf', { hasText: 'Cơ hội và hồ sơ thầu' }).first().click();
        await p.locator('.o_action_manager .o_list_view').first().waitFor({ timeout: 30000 });
        await p.locator('.o_tp_kd_sb_leaf', { hasText: 'Tổng quan' }).first().click();
        await ready(p);
      }
      check('D3 enter/leave ×5: one root, no errors', await p.locator('.o_tp_kd_ov').count() === 1 && errors.length === before, errors.slice(before, before + 3));
      await context.close();
    }
  });

  // ------------------------------------------------------------ D. layout, viewports, zoom, sidebar, other apps
  await section('layout', async () => {
    const sizes = [
      ...ctx.VIEWPORTS.map(([w, h]) => ({ name: `${w}x${h}`, contextOptions: { viewport: { width: w, height: h } } })),
      { name: 'zoom125-1440x900', contextOptions: { viewport: { width: 1152, height: 720 }, deviceScaleFactor: 1.25 } },
      { name: 'zoom150-1440x900', contextOptions: { viewport: { width: 960, height: 600 }, deviceScaleFactor: 1.5 } },
    ];
    for (const size of sizes) {
      const { context, p } = await open('reviewer', { contextOptions: size.contextOptions });
      const f = await p.evaluate(layoutFacts);
      evidence.layout[size.name] = f;
      check(`D5 ${size.name} no horizontal scroll`, f.docOverflow <= 1 && f.ovOverflow <= 1, [f.docOverflow, f.ovOverflow]);
      check(`D6 ${size.name} one vertical scroller`, f.pageScroll <= 1 && f.overflowY === 'auto', [f.pageScroll, f.overflowY]);
      if (size.name === '1440x900') {
        check('D4 1440×900 first screen: header, filters, KPIs, main pair', f.head < f.filters && f.filters < f.kpis && f.pairBottom <= f.innerHeight
          && Math.abs(f.d01.top - f.g01.top) < 2 && f.d01.width < f.g01.width, f);
      }
      if (size.name === '390x844') check('D5 390 KPIs 2×2', new Set(f.kpiTops).size === 2, f.kpiTops);
      // D6 wheel over the page scrolls the Overview root
      const box = await p.locator('.o_tp_kd_kpis').first().boundingBox();
      await p.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await p.mouse.wheel(0, 600);
      await p.waitForTimeout(400);
      const top = await p.evaluate(() => document.querySelector('.o_tp_kd_ov').scrollTop);
      check(`D6 ${size.name} mouse wheel scrolls`, top > 0 || f.ovRoom <= 0, [top, f.ovRoom]);
      await p.evaluate(() => { document.querySelector('.o_tp_kd_ov').scrollTop = 0; });
      await p.waitForTimeout(200);
      await shot(p, `after-overview-${size.name}`);
      if (['1440x900', '390x844'].includes(size.name)) await shotFull(p, `after-overview-${size.name.split('x')[0]}-full`);
      if (size.name === '390x844') {
        await p.locator('.o_tp_kd_filters_toggle').click();
        await p.waitForTimeout(300);
        check('D5 390 filters open on demand', await p.locator('#tp_kd_filters_body').isVisible()
          && await p.locator('.o_tp_kd_filters_toggle').getAttribute('aria-expanded') === 'true');
        await shot(p, 'after-filters-390');
        await p.locator('.o_tp_kd_filters_toggle').click();
        await p.locator('.o_tp_kd_d01 .o_tp_kd_dleg:not([disabled])').first().click();
        await p.locator('.o_tp_kd_pick').first().scrollIntoViewIfNeeded();
        await shot(p, 'after-select-390');
      }
      if (size.name === '1440x900') {
        await p.locator('.o_tp_kd_sb_collapse').first().click();
        await p.waitForTimeout(400);
        const c = await p.evaluate(layoutFacts);
        evidence.layout['1440x900-collapsed'] = c;
        check('D5 sidebar collapsed: no h-scroll, pair side by side', c.docOverflow <= 1 && c.ovOverflow <= 1 && Math.abs(c.d01.top - c.g01.top) < 2, c);
        await shot(p, 'after-overview-1440x900-collapsed');
        await p.locator('.o_tp_kd_sb_collapse').first().click();
      }
      await context.close();
    }
    // D7 other apps keep their own styles
    const { context, p } = await open('reviewer');
    const apps = {};
    for (const [name, url] of [['discuss', '/odoo/discuss'], ['crm', '/odoo/crm']]) {
      await p.goto(`${ctx.base}${url}`);
      await p.waitForTimeout(2500);
      apps[name] = await p.evaluate(() => {
        const action = document.querySelector('.o_action_manager > .o_action');
        return { ov: document.querySelectorAll('.o_tp_kd_ov').length, token: action ? getComputedStyle(action).getPropertyValue('--kd-bg').trim() : null,
          bodyToken: getComputedStyle(document.body).getPropertyValue('--kd-bg').trim(), url: location.pathname };
      });
    }
    evidence.layout.apps = apps;
    check('D7 other apps get no Overview style', Object.values(apps).every(a => a.ov === 0 && !a.token && !a.bodyToken), apps);
    await context.close();
  });

  evidence.failures = failures;
  fs.writeFileSync(path.join(out, 'overview-evidence.json'), JSON.stringify(evidence, null, 2));
  ctx.check(`overview checks (${failures.length} failed)`, failures.length === 0, failures);
};
