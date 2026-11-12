/* KD-UI-003 after/verify checks (B1–B20). Clone: full set incl. write chains. Dev: read-only smoke.
 * Private output (images, JSON) stays in .local/kd-ui003/shots/<target>-<mode>/. */
const fs = require('node:fs');
const path = require('node:path');

const DEFAULT_KD_LINE = 'rgb(217, 226, 236)';
const DEFAULT_KD_HEAD = 'rgb(238, 243, 248)';
const LABEL = {
  overview: 'Tổng quan', opportunities: 'Cơ hội và hồ sơ thầu', projects: 'Hồ sơ dự án',
  contracts: 'Hợp đồng và phụ lục', tasks: 'Kế hoạch và công việc', allocations: 'Giao khoán và thầu phụ',
  productions: 'Sản lượng theo kỳ', acceptances: 'Hồ sơ nghiệm thu', plans: 'Kế hoạch định kỳ',
  payments: 'Đề nghị thanh toán', credentials: 'Năng lực và chứng chỉ', obligations: 'Nghĩa vụ và hồ sơ còn thiếu',
};
const DOSSIERS = {
  allocations: ['tp.allocation', ['Phạm vi / đầu ra', 'Khoán cấp 2', 'Giá trị minh họa', 'Lịch sử lần trình']],
  productions: ['tp.production', ['Phạm vi / đầu ra', 'Giá trị minh họa', 'Lịch sử lần trình']],
  acceptances: ['tp.acceptance', ['Phạm vi / đầu ra', 'Kiểm kê căn cứ', 'Giá trị minh họa', 'Lịch sử lần trình']],
  payments: ['tp.payment.request', ['Nội dung / phạm vi', 'Chứng từ và đối chiếu', 'Giá trị minh họa', 'Lịch sử lần trình']],
  plans: ['tp.periodic.plan', ['Phạm vi', 'Chỉ tiêu và đối chiếu nguồn', 'Lịch sử lần trình']],
  credentials: ['tp.credential', ['Phạm vi năng lực', 'Nguồn / xác minh', 'Lịch sử lần trình']],
  obligations: ['tp.obligation', ['Yêu cầu / phạm vi', 'Danh mục hồ sơ', 'Lịch sử lần trình']],
};

// Runs inside the page: measurable table facts (no DOM writes).
function tableFacts() {
  const view = document.querySelector('.o_list_view');
  if (!view) return null;
  const renderer = view.querySelector('.o_list_renderer');
  if (!renderer) return null;
  const rs = getComputedStyle(renderer);
  const ths = [...view.querySelectorAll('thead th')];
  const rows = [...view.querySelectorAll('tbody tr.o_data_row')];
  const cells = rows[0] ? [...rows[0].querySelectorAll('td')] : [];
  const inner = cells.filter((td, i) => !td.classList.contains('o_list_record_selector') && i < cells.length - 1);
  const label = th => th.querySelector('.text-truncate') || th;
  const td0 = inner[0];
  return {
    classes: view.className,
    shell: document.body.classList.contains('o_tp_kd_shell'),
    border: `${rs.borderTopWidth} ${rs.borderTopColor}`,
    radius: rs.borderTopLeftRadius,
    headBg: ths[1] ? getComputedStyle(ths[1]).backgroundColor : null,
    // Odoo makes the <thead> sticky (desktop >= md), not each <th>.
    sticky: view.querySelector('.o_list_table thead') ? getComputedStyle(view.querySelector('.o_list_table thead')).position : null,
    lines: [...new Set(inner.map(td => `${getComputedStyle(td).borderRightWidth} ${getComputedStyle(td).borderRightColor}`))],
    rowLine: rows[0] ? getComputedStyle(rows[0]).borderBottomWidth : null,
    firstCellLine: td0 ? `${getComputedStyle(td0).borderRightWidth} ${getComputedStyle(td0).borderRightColor}` : null,
    selectorLine: cells.find(td => td.classList.contains('o_list_record_selector'))
      ? getComputedStyle(cells.find(td => td.classList.contains('o_list_record_selector'))).borderRightWidth : null,
    headTruncated: ths.filter(th => label(th).scrollWidth > label(th).clientWidth + 1).map(th => th.innerText.trim()),
    wrapTruncated: [...view.querySelectorAll('td.tp_kd_wrap')].filter(td => td.scrollWidth > td.clientWidth + 1).map(td => td.innerText.slice(0, 40)),
    badgeTruncated: [...view.querySelectorAll('td.o_badge_cell .badge,td .tp_kd_badge')].filter(b => {
      const cell = b.closest('td'), range = document.createRange(); range.selectNodeContents(b);
      const bounds = cell.getBoundingClientRect();
      return b.scrollWidth > b.clientWidth + 1 || [...range.getClientRects()].some(r =>
        r.right > bounds.right + 1 || r.left < bounds.left - 1 || r.bottom > bounds.bottom + 1);
    }).map(b => b.innerText),
    widths: Object.fromEntries(ths.filter(th => th.dataset.name).map(th => [th.dataset.name, Math.round(th.getBoundingClientRect().width)])),
    rows: rows.length,
    rowHeights: rows.map(r => Math.round(r.getBoundingClientRect().height)),
    docOverflow: document.documentElement.scrollWidth - window.innerWidth,
    rendererOverflow: renderer.scrollWidth - renderer.clientWidth,
    pager: document.querySelector('.o_pager_value')?.innerText.trim(),
    total: document.querySelector('.o_pager_limit')?.innerText.trim(),
    active: document.querySelector('.o_tp_kd_sb_leaf[aria-current="page"]')?.innerText.trim() || null,
    tools: !!document.querySelector('.o_tp_kd_list_tools'),
  };
}

function formFacts() {
  const form = document.querySelector('.o_action_manager .o_form_view');
  if (!form) return null;
  const visible = el => !!el.getClientRects().length;
  const fields = [...form.querySelectorAll('.o_inner_group .o_field_widget.o_readonly_modifier')].filter(visible);
  const emptyFields = fields.filter(f => !f.innerText.trim() && !f.querySelector('input, img, canvas, .o-checkbox, button'));
  const dash = el => [el, el.firstElementChild].filter(Boolean).some(x => getComputedStyle(x, '::before').content === '"—"');
  return {
    classes: form.className,
    separators: [...form.querySelectorAll('.o_horizontal_separator')].filter(visible).map(s => s.innerText.trim()),
    tabs: [...form.querySelectorAll('.o_notebook .nav-link')].filter(visible).map(t => t.innerText.trim()),
    saveButtons: [...document.querySelectorAll('.o_form_button_save')].filter(visible).length,
    emptyReadonly: emptyFields.map(f => f.getAttribute('name')),
    emptyWithoutDash: emptyFields.filter(f => !dash(f)).map(f => f.getAttribute('name')),
    emptyDoubleDash: emptyFields.filter(f => [f, ...f.querySelectorAll('*')].filter(x => getComputedStyle(x, '::before').content === '"—"').length > 1).map(f => f.getAttribute('name')),
    groupLefts: [...new Set([...form.querySelectorAll('.o_inner_group')].filter(visible).map(g => Math.round(g.getBoundingClientRect().left)))],
    docOverflow: document.documentElement.scrollWidth - window.innerWidth,
    active: document.querySelector('.o_tp_kd_sb_leaf[aria-current="page"]')?.innerText.trim() || null,
    hasAmountIds: !!form.querySelector('[name="amount_ids"]'),
    buttons: [...document.querySelectorAll('.o_form_view .o_statusbar_buttons button')].filter(visible).map(b => b.innerText.trim()),
  };
}

module.exports = async function after(ctx) {
  const KD_LINE = ctx.tableTokens?.line || DEFAULT_KD_LINE;
  const KD_HEAD = ctx.tableTokens?.head || DEFAULT_KD_HEAD;
  const { browser, base, login, ok, watch, shot, out, errors, target, LEAVES } = ctx;
  // Odoo keeps a long-lived bus connection, so "networkidle" can take the full default timeout.
  // Wait briefly for it, then for the action's own busy markers to clear.
  const settle = async p => {
    if (ctx.settle) return ctx.settle(p);
    await p.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => {});
    await p.waitForFunction(() => !document.querySelector('.o_loading_indicator, .o_view_nocontent_loading'), null, { timeout: 8000 }).catch(() => {});
    await p.waitForTimeout(350);
  };
  const openList = async (p, action) => {
    const response = await p.context().request.post(`${base}/web/action/load`, {
      data: { jsonrpc: '2.0', method: 'call', params: { action_id: action } },
    });
    const loaded = (await response.json()).result;
    if (!loaded?.id) throw new Error(`Cannot resolve action ${action}`);
    await p.goto(`${base}/odoo/action-${loaded.id}`, { timeout: 120000 });
    await p.locator('.o_list_view').first().waitFor({ timeout: 60000 });
    await settle(p);
  };
  const openFirst = async p => {
    await p.locator('.o_list_view .o_data_row .o_data_cell').first().click();
    await p.locator('.o_action_manager .o_form_view').first().waitFor({ timeout: 30000 });
    await settle(p);
  };
  const write = target === 'clone';  // dev: read-only smoke, never a write chain, typed edit or wizard
  const stage = process.env.KD_STAGE || 'all';
  const evidence = { tables: {}, forms: {}, chains: {}, roles: {}, responsive: {}, leak: {}, overview: {} };
  const ACTION = Object.fromEntries(LEAVES);
  const run = name => stage === 'all' || stage.split(',').includes(name);
  // Every check is recorded; one failure does not hide the rest. The run fails at the end.
  const failures = [];
  const check = (name, condition, detail) => {
    try { ctx.check(name, condition, detail); } catch (error) { failures.push(error.message.slice(0, 600)); }
  };
  async function section(name, body) {
    if (!run(name)) return;
    const started = Date.now();
    try {
      await body();
    } catch (error) {
      failures.push(`[${name}] aborted: ${String(error.message || error).split('\n')[0].slice(0, 400)}`);
    }
    evidence[`time_${name}`] = Math.round((Date.now() - started) / 1000);
  }

  async function page(context) {
    const p = await context.newPage();
    p.setDefaultTimeout(30000);
    watch(p);
    return p;
  }
  async function clickLeaf(p, key) {
    // Wait for the previous action to leave the DOM, then for the new one (no stale match).
    const previous = await p.locator('.o_action_manager > .o_action').first().elementHandle().catch(() => null);
    // Below 768px the sidebar is a drawer: open it with "Menu KH-KD" like a phone user.
    const toggle = p.locator('.o_tp_kd_menu_toggle');
    if (await toggle.isVisible().catch(() => false)) await toggle.click();
    await p.locator('.o_tp_kd_sb_leaf', { hasText: LABEL[key] }).first().click();
    if (previous) await p.waitForFunction(el => !el.isConnected, previous, { timeout: 20000 });
    await (key === 'overview' ? p.locator('.o_tp_kd_ov').first() : p.locator('.o_list_view').first()).waitFor();
    await settle(p);
  }
  async function openLeaf(p, key) {
    if (key === 'contracts') {
      // Same route as a user: the KH-KD sidebar leaf (direct URL would open the TP Contracts app).
      await openList(p, ACTION.tasks);
      await clickLeaf(p, 'contracts');
    } else {
      await openList(p, ACTION[key]);
    }
  }
  const facts = async p => { await p.locator('.o_list_view .o_list_renderer').first().waitFor(); return p.evaluate(tableFacts); };
  const form = p => p.evaluate(formFacts);
  function assertTable(key, f, width) {
    check(`B1 ${key}@${width} KH-KD shell + table class`, f.shell && f.classes.includes('tp_kd_table'), f.classes);
    check(`B1 ${key}@${width} frame 1px line + radius 8px`, f.border === `1px ${KD_LINE}` && f.radius === '8px', [f.border, f.radius]);
    check(`B1 ${key}@${width} header background`, f.headBg === KD_HEAD, f.headBg);
    if (f.rows) {
      check(`B1 ${key}@${width} vertical cell lines`, f.lines.length === 1 && f.lines[0] === `1px ${ctx.tableTokens?.cellLine || KD_LINE}`, f.lines);
      check(`B1 ${key}@${width} row bottom line`, f.rowLine === '1px', f.rowLine);
      if (f.selectorLine !== null) check(`B1 ${key}@${width} checkbox column has no vertical rule`, f.selectorLine === '0px', f.selectorLine);
    }
    check(`B2 ${key}@${width} headers not truncated`, f.headTruncated.length === 0, f.headTruncated);
    check(`B2 ${key}@${width} wrapped cells not truncated`, f.wrapTruncated.length === 0, f.wrapTruncated);
    check(`B2 ${key}@${width} status badges read in full`, f.badgeTruncated.length === 0, f.badgeTruncated);
    check(`B3/B16 ${key}@${width} no page horizontal scroll`, f.docOverflow <= 1, f.docOverflow);
    if (width >= 768) check(`B4 ${key}@${width} sticky header`, f.sticky === 'sticky', f.sticky);
  }

  // ------------------------------------------------------------ B1–B4, B10, B11 on every leaf (reviewer)
  await section('tables', async () => {
    const context = await login(browser, 'reviewer');
    for (const [key] of LEAVES) {
      const p = await page(context);
      await openLeaf(p, key);
      const f = await facts(p);
      evidence.tables[key] = f;
      assertTable(key, f, 1440);
      check(`B10 ${key} sidebar leaf active`, (f.active || '').startsWith(LABEL[key].split(' — ')[0]), f.active);
      check(`B7 ${key} server pager present`, !!f.pager, f);
      if (key !== 'contracts') check(`B7 ${key} page size 20`, f.rows <= 20 && (Number(f.total) <= 20 || f.pager.startsWith('1-20')), [f.pager, f.total, f.rows]);
      await shot(p, `list-${key}-1440`);
      if (f.rows) {
        await openFirst(p);
        const ff = await form(p);
        evidence.forms[key] = ff;
        await shot(p, `form-${key}-1440`, true);
        check(`B10 ${key} form keeps leaf active`, (ff.active || '').startsWith(LABEL[key].split(' — ')[0]), ff.active);
        check(`B11 ${key} one save button at most`, ff.saveButtons <= 1, ff.saveButtons);
        check(`B11 ${key} empty read-only values show "—"`, ff.emptyWithoutDash.length === 0, ff.emptyWithoutDash);
        check(`B11 ${key} empty read-only values show a single "—"`, ff.emptyDoubleDash.length === 0, ff.emptyDoubleDash);
        check(`B11 ${key} form KH-KD class`, ff.classes.includes('tp_kd_form'), ff.classes);
        if (DOSSIERS[key]) {
          check(`B11 ${key} block titles`, ['Căn cứ và dự án', 'Phụ trách và hạn'].every(t => ff.separators.some(s => s.toLowerCase() === t.toLowerCase())) && ff.separators.length >= 3, ff.separators);
          check(`B11 ${key} notebook order`, JSON.stringify(ff.tabs) === JSON.stringify(DOSSIERS[key][1]), ff.tabs);
        }
        if (key === 'payments') {
          await p.locator('.o_notebook .nav-link', { hasText: 'Giá trị minh họa' }).click();
          await settle(p);
          const sub = await p.evaluate(() => {
            const r = document.querySelector('.o_form_view .o_field_x2many .o_list_renderer');
            return r && { border: getComputedStyle(r).borderTopWidth, radius: getComputedStyle(r).borderTopLeftRadius };
          });
          evidence.forms.paymentsMoney = sub;
          check('B11 money sub-table bordered (reviewer)', !sub || (sub.border === '1px' && sub.radius === '8px'), sub);
          await shot(p, 'form-payments-money-reviewer-1440', true);
        }
        if (key === 'projects') {
          await p.reload();
          await p.locator('.o_form_view').first().waitFor();
          await settle(p);
          check('B10 refresh project form keeps leaf', ((await form(p)).active || '').startsWith('Hồ sơ dự án'));
        }
      }
      await p.close();
    }
    await context.close();
  });

  // ------------------------------------------------------------ B3–B9, B17 on WBS (reviewer)
  await section('behaviour', async () => {
    const context = await login(browser, 'reviewer');
    let p = await page(context);
    await openLeaf(p, 'tasks');
    let f = await facts(p);
    evidence.tables.tasksWidths = f.widths;
    const minimum = { name: 240, project_id: 220, kd_responsible_id: 190, date_deadline: 130, state: 130 };
    check('B3 WBS column minimums at 1440', Object.entries(minimum).every(([n, w]) => (f.widths[n] || 0) >= w), f.widths);

    // B4: scroll inside the renderer, header stays at its top.
    const sticky = await p.evaluate(() => {
      const r = document.querySelector('.o_list_view .o_list_renderer');
      r.scrollTop = 240;
      const th = r.querySelector('thead th:nth-of-type(2)') || r.querySelector('thead th');
      return { scrolled: r.scrollTop, delta: Math.round(th.getBoundingClientRect().top - r.getBoundingClientRect().top) };
    });
    evidence.tables.sticky = sticky;
    check('B4 header stays on top of the scrolled list', sticky.scrolled === 0 || Math.abs(sticky.delta) <= 2, sticky);
    await shot(p, 'list-tasks-scrolled-1440');
    await p.evaluate(() => { document.querySelector('.o_list_view .o_list_renderer').scrollTop = 0; });

    // B5: optional column on, survives reload, "Khôi phục cột" resets; foreign keys untouched.
    await p.evaluate(() => {
      localStorage.setItem('optional_fields,crm.lead,list,1,name', 'kd-ui003-sentinel');
      localStorage.setItem('kd_ui003_foreign_key', 'keep');
    });
    await p.locator('.o_optional_columns_dropdown_toggle').first().click();
    await p.locator('.o-dropdown--menu .o-dropdown-item, .o-dropdown--menu .dropdown-item').filter({ hasText: 'Đầu ra' }).first().click();
    await settle(p);
    check('B5 optional column shown', await p.locator('th[data-name="kd_deliverable"]').count() === 1);
    await p.keyboard.press('Escape');
    await p.reload();
    await p.locator('.o_list_view').first().waitFor();
    await settle(p);
    check('B5 optional column persists after reload', await p.locator('th[data-name="kd_deliverable"]').count() === 1);
    await shot(p, 'list-tasks-optional-1440');
    if (await p.locator('.tp_kd_display_options:not([open])').count()) await p.locator('.tp_kd_display_options summary').click();
    await p.locator('.o_tp_kd_reset_columns').click();
    await settle(p);
    check('B5 reset columns hides it again', await p.locator('th[data-name="kd_deliverable"]').count() === 0);
    const foreign = await p.evaluate(() => [localStorage.getItem('optional_fields,crm.lead,list,1,name'), localStorage.getItem('kd_ui003_foreign_key')]);
    check('B5 reset leaves non-KH-KD keys alone', foreign[0] === 'kd-ui003-sentinel' && foreign[1] === 'keep', foreign);
    await p.evaluate(() => { localStorage.removeItem('optional_fields,crm.lead,list,1,name'); localStorage.removeItem('kd_ui003_foreign_key'); });

    // B6: density compact / comfortable, persisted.
    if (await p.locator('.tp_kd_display_options:not([open])').count()) await p.locator('.tp_kd_display_options summary').click();
    await p.locator('.o_tp_kd_density button', { hasText: 'Gọn' }).click();
    await settle(p);
    f = await facts(p);
    const compactMin = Math.min(...f.rowHeights);
    check('B6 compact rows 36–40px', compactMin >= 36 && compactMin <= 41, f.rowHeights.slice(0, 6));
    await shot(p, 'list-tasks-compact-1440');
    await p.reload();
    await p.locator('.o_list_view').first().waitFor();
    await settle(p);
    check('B6 compact persists after reload', await p.evaluate(() => document.body.classList.contains('o_tp_kd_compact')));
    if (await p.locator('.tp_kd_display_options:not([open])').count()) await p.locator('.tp_kd_display_options summary').click();
    await p.locator('.o_tp_kd_density button', { hasText: 'Thoáng' }).click();
    await settle(p);
    f = await facts(p);
    const comfyMin = Math.min(...f.rowHeights);
    check('B6 comfortable rows 44–52px', comfyMin >= 44 && comfyMin <= 53, f.rowHeights.slice(0, 6));
    check('B6 back to comfortable', !(await p.evaluate(() => document.body.classList.contains('o_tp_kd_compact'))));

    // B7: server paging (offset/limit in the request) and server sort.
    const first = await p.locator('.o_data_row').first().innerText();
    const nextReq = p.waitForRequest(r => r.url().includes('web_search_read') && /"offset":\s*20/.test(r.postData() || '') && /"limit":\s*20/.test(r.postData() || ''));
    await p.locator('.o_pager_next').click();
    await nextReq;
    await settle(p);
    f = await facts(p);
    check('B7 page 2 from server', f.pager.startsWith('21-') && (await p.locator('.o_data_row').first().innerText()) !== first, f.pager);
    await p.locator('.o_pager_previous').click();
    await settle(p);
    const sortReq = p.waitForRequest(r => r.url().includes('web_search_read') && (r.postData() || '').includes('date_deadline'));
    await p.locator('th[data-name="date_deadline"]').click();
    const sortBody = (await sortReq).postData();
    await settle(p);
    check('B7 header sort is a server order with limit 20', /"order":\s*"date_deadline/.test(sortBody) && /"limit":\s*20/.test(sortBody), sortBody.slice(0, 300));
    await p.locator('th[data-name="date_deadline"]').click();
    await settle(p);

    // B8: group by + checkbox selection.
    await p.locator('.o_searchview_dropdown_toggler').click();
    const groupItem = p.locator('.o_group_by_menu .o-dropdown-item, .o_group_by_menu .dropdown-item, .o_group_by_menu span').filter({ hasText: /^Dự án$/ }).first();
    if (await groupItem.count()) {
      await groupItem.click();
      await settle(p);
      await p.keyboard.press('Escape');
      const groups = await p.evaluate(() => [...document.querySelectorAll('.o_list_view tr.o_group_header')].map(g => getComputedStyle(g).borderBottomWidth));
      check('B8 group headers with a line', groups.length > 0 && groups.every(w => w === '1px'), groups.slice(0, 3));
      await shot(p, 'list-tasks-grouped-1440');
      await p.locator('.o_facet_remove').first().click();
      await settle(p);
    } else {
      await p.keyboard.press('Escape');
      evidence.tables.groupBy = 'group-by item "Dự án" not offered in this search view';
    }
    await p.locator('.o_data_row .o_list_record_selector input').first().check();
    await settle(p);
    check('B8 checkbox selects without opening form', await p.locator('.o_data_row_selected').count() === 1 && await p.locator('.o_action_manager .o_form_view').count() === 0);
    check('B8 table tools step aside while selecting', await p.locator('.o_tp_kd_list_tools').count() === 0);
    await shot(p, 'list-tasks-selected-1440');
    await p.locator('.o_data_row .o_list_record_selector input').first().uncheck();
    await settle(p);

    // B9: page 2 → open → (edit + discard on clone) → breadcrumb back to page 2.
    await p.locator('.o_pager_next').click();
    await settle(p);
    await openFirst(p);
    const nameInput = p.locator('.o_form_view .o_field_widget[name="name"] input, .o_form_view .o_field_widget[name="name"] textarea').first();
    if (write && await nameInput.count()) {
      const before = await nameInput.inputValue();
      await nameInput.fill(`${before} (thử bỏ)`);
      await p.locator('.o_form_button_cancel').first().click();
      await settle(p);
      check('B9 discard restores value', (await nameInput.inputValue()) === before);
    }
    await p.locator('.o_breadcrumb .breadcrumb-item a, .o_back_button').first().click();
    await p.locator('.o_list_view').first().waitFor();
    await settle(p);
    check('B9 breadcrumb back keeps page', (await facts(p)).pager.startsWith('21-'));

    // B17: keyboard Enter opens a row.
    await p.locator('.o_pager_previous').click();
    await settle(p);
    await p.locator('.o_data_row .o_data_cell').first().focus();
    await p.keyboard.press('Enter');
    await p.locator('.o_action_manager .o_form_view').first().waitFor();
    check('B17 keyboard Enter opens the record', true);
    await p.close();
    await context.close();

    // B17: touch + reduced motion.
    const touch = await login(browser, 'reviewer', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
    p = await page(touch);
    await openLeaf(p, 'tasks');
    const transition = await p.evaluate(() => getComputedStyle(document.querySelector('.o_data_row td:not(.o_list_record_selector)')).transitionDuration);
    check('B17 reduced motion: no transition', transition === '0s', transition);
    await p.locator('.o_data_row .o_data_cell').first().tap();
    await p.locator('.o_action_manager .o_form_view').first().waitFor();
    check('B17 touch tap opens the record', true);
    await touch.close();
  });

  // ------------------------------------------------------------ B10 sidebar from overview / project table
  await section('sidebar', async () => {
    const context = await login(browser, 'reviewer');
    const p = await page(context);
    await p.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`);
    await p.locator('.o_tp_kd_ov').first().waitFor();
    await settle(p);
    const total = p.locator('.o_tp_kd_total_btn').first();
    if (await total.count()) {
      await total.click();
      await p.locator('.o_list_view').first().waitFor();
      await settle(p);
      check('B10 overview → opportunities marks Cơ hội', ((await facts(p)).active || '').startsWith('Cơ hội'));
      await p.locator('.o_breadcrumb .breadcrumb-item a').first().click();
      await p.locator('.o_tp_kd_ov').first().waitFor();
      await settle(p);
      check('B10 breadcrumb back marks Tổng quan', (await p.evaluate(() => document.querySelector('.o_tp_kd_sb_leaf[aria-current="page"]')?.innerText.trim())) === 'Tổng quan');
    }
    const proj = p.locator('.o_tp_kd_proj_name').first();
    if (await proj.count()) {
      await proj.click();
      await p.locator('.o_form_view').first().waitFor();
      await settle(p);
      check('B10 overview project row → Hồ sơ dự án', ((await form(p)).active || '').startsWith('Hồ sơ dự án'));
      await p.reload();
      await p.locator('.o_form_view').first().waitFor();
      await settle(p);
      check('B10 refresh keeps Hồ sơ dự án', ((await form(p)).active || '').startsWith('Hồ sơ dự án'));
    }
    await clickLeaf(p, 'contracts');
    check('B10 contracts menu → Hợp đồng leaf', ((await facts(p)).active || '').startsWith('Hợp đồng'));
    await context.close();
  });

  // ------------------------------------------------------------ B12 / B13 write chains (clone only)
  const choose = async (p, name, text) => {
    const input = p.locator(`.modal [name="${name}"] input`).first();
    await input.click();
    await input.fill(text);
    await p.getByRole('option').filter({ hasText: text }).first().click({ timeout: 10000 });
  };
  const fillModal = (p, name, value) => p.locator(`.modal [name="${name}"] input, .modal [name="${name}"] textarea`).first().fill(value);
  const confirm = async (p, text) => {
    await p.locator('.modal footer').last().getByRole('button', { name: text, exact: true }).click();
    try {
      // Wait for every dialog to close (a wizard may sit under a short-lived second dialog).
      await p.waitForFunction(() => !document.querySelector('.modal'), null, { timeout: 30000 });
    } catch (error) {
      const titles = await p.locator('.modal .modal-title').allInnerTexts();
      const bodies = await p.locator('.modal .modal-body').allInnerTexts();
      await shot(p, `confirm-stuck-${text.replace(/\s+/g, '-')}-1440`);
      throw new Error(`dialogs still open after "${text}": ${JSON.stringify(titles)} ${JSON.stringify(bodies.map(b => b.slice(0, 200)))}`);
    }
    await settle(p);
  };
  const userId = async (context, key) => (await ok(context, 'res.users', 'search_read', [[['login', '=', ctx.actors[key].login]], ['id', 'name']]))[0];

  if (write) await section('contract', async () => {
    const editor = await login(browser, 'editor');
    const reviewer = await login(browser, 'reviewer');
    const reviewerName = (await userId(reviewer, 'reviewer')).name;
    const ep = await page(editor);
    await openLeaf(ep, 'contracts');
    await ep.getByRole('button', { name: 'Tạo nháp hợp đồng', exact: true }).click();
    await ep.locator('.modal .o_form_view').first().waitFor();
    check('B12 contract wizard styled inside KH-KD', await ep.locator('.modal .o_form_view.tp_kd_form').count() === 1 && await ep.evaluate(() => document.body.classList.contains('o_tp_kd_shell')));
    const projectInput = ep.locator('.modal [name="project_id"] input').first();
    await projectInput.click();
    await ep.locator('.o-autocomplete--dropdown-menu [role="option"]').first().click();
    const code = `KD-UI3-HD-${Date.now()}`;
    await fillModal(ep, 'code', code);
    await fillModal(ep, 'name', 'Hợp đồng kiểm thử bảng KD-UI-003');
    await fillModal(ep, 'revision_name', 'Bản gốc KD-UI-003');
    await choose(ep, 'currency_id', 'VND');
    await ep.locator('.modal [name="line_ids"] .o_field_x2many_list_row_add a, .modal [name="line_ids"] .o_field_x2many_list_row_add button').first().click();
    await ep.locator('.modal [name="line_ids"] [name="scope_key"] input').fill('KS');
    await ep.locator('.modal [name="line_ids"] [name="name"] input').fill('Khảo sát hiện trường');
    // Submit needs every scope line to carry a confirmed value (backend rule `amounts_not_confirmed`).
    await ep.locator('.modal .o_notebook .nav-link').filter({ hasText: 'Nhập giá trị mới' }).click();
    await ep.locator('.modal [name="amount_input_ids"] .o_field_x2many_list_row_add a, .modal [name="amount_input_ids"] .o_field_x2many_list_row_add button').first().click();
    await ep.locator('.modal [name="amount_input_ids"] [name="scope_key"] input').fill('KS');
    // Odoo 20 selection fields render a SelectMenu dropdown, not a native <select>.
    const pick = async (field, label) => {
      await ep.locator(`.modal [name="amount_input_ids"] [name="${field}"] .o_select_menu_toggler`).first().click();
      await ep.locator('.o_field_selection_menu [data-choice-index]').filter({ hasText: label }).first().click();
    };
    await pick('amount_state', 'Đã xác nhận');
    await ep.locator('.modal [name="amount_input_ids"] [name="value"] input').fill('100000000');
    await pick('tax_basis', 'Chưa thuế');
    await shot(ep, 'contract-wizard-kd-1440');
    await confirm(ep, 'Lưu nháp');
    const contract = (await ok(editor, 'tp.contract', 'search_read', [[['code', '=', code]], ['aggregate_version']]))[0];
    const revision = (await ok(editor, 'tp.contract.revision', 'search_read', [[['contract_id', '=', contract.id]], ['review_state']]))[0];
    evidence.chains.contract = { code, contract: contract.id, revision: revision.id };
    check('B12 draft created', revision.review_state === 'draft');
    const openRevision = async p => { await p.goto(`${base}/odoo/tp.contract.revision/${revision.id}`); await p.locator('.o_form_view').first().waitFor(); await settle(p); };
    await openRevision(ep);
    await ep.getByRole('button', { name: 'Chỉnh sửa nháp', exact: true }).click();
    await fillModal(ep, 'revision_name', 'Tên chưa lưu vì version cũ');
    const concurrent = await ok(editor, 'tp.contract.native.draft', 'create', [{ contract_id: contract.id, revision_id: revision.id, revision_name: 'Bản gốc KD-UI-003 (đồng thời)' }]);
    await ok(editor, 'tp.contract.native.draft', 'action_confirm', [[concurrent]]);
    await ep.locator('.modal footer').getByRole('button', { name: 'Lưu nháp', exact: true }).click();
    await ep.getByText(/Hồ sơ vừa được cập nhật ở nơi khác/).first().waitFor();
    check('B12 stale version reports a conflict', true);
    await shot(ep, 'contract-stale-1440');
    await ep.getByRole('button', { name: 'Tải lại hồ sơ', exact: true }).click();
    await settle(ep);
    await openRevision(ep);
    await ep.getByRole('button', { name: 'Chỉnh sửa nháp', exact: true }).click();
    await fillModal(ep, 'revision_name', 'Bản gốc KD-UI-003 đã sửa');
    await confirm(ep, 'Lưu nháp');
    await ep.getByRole('button', { name: 'Trình rà soát', exact: true }).click();
    try {
      await choose(ep, 'reviewer_id', reviewerName);
    } catch (error) {
      evidence.chains.contract.reviewer = `"${reviewerName}" is not offered as contract reviewer here; chain stops at submit (covered by tp_contract tests)`;
      await shot(ep, 'contract-submit-reviewer-1440');
      throw error;
    }
    await confirm(ep, 'Trình rà soát');
    const rp = await page(reviewer);
    await openRevision(rp);
    await rp.getByRole('button', { name: 'Trả lại để chỉnh sửa', exact: true }).click();
    await fillModal(rp, 'reason', 'KD-UI-003: cần bổ sung phạm vi');
    await confirm(rp, 'Trả lại để chỉnh sửa');
    await openRevision(ep);
    await ep.getByRole('button', { name: 'Bắt đầu chỉnh sửa lại', exact: true }).click();
    await fillModal(ep, 'reason', 'Bổ sung theo ý kiến rà soát');
    await confirm(ep, 'Bắt đầu chỉnh sửa lại');
    await ep.getByRole('button', { name: 'Chỉnh sửa nháp', exact: true }).click();
    await fillModal(ep, 'revision_name', 'Bản gốc KD-UI-003 bổ sung');
    await confirm(ep, 'Lưu nháp');
    await ep.getByRole('button', { name: 'Trình rà soát lại', exact: true }).click();
    await choose(ep, 'reviewer_id', reviewerName);
    await fillModal(ep, 'fix_summary', 'Đã bổ sung phạm vi');
    await confirm(ep, 'Trình rà soát');
    const submissions = await ok(editor, 'tp.contract.submission', 'search_read', [[['revision_id', '=', revision.id]], ['sequence', 'outcome']]);
    evidence.chains.contract.submissions = submissions;
    check('B12 draft → submit → return → rework → resubmit', submissions.length === 2 && submissions.some(s => s.outcome === 'pending'), submissions);
    await shot(ep, 'contract-resubmitted-1440', true);
    await editor.close();
    await reviewer.close();
  });

  if (write) await section('dossier', async () => {
    // B13 one dossier type (payment request) through the KH-KD transition dialog.
    const editor = await login(browser, 'editor');
    const reviewer = await login(browser, 'reviewer');
    const owner = await userId(editor, 'editor');
    const rev = await userId(reviewer, 'reviewer');
    const [dossier] = await ok(editor, 'tp.payment.request', 'search_read',
      [[['state', '=', 'draft'], ['owner_id', '=', owner.id], ['reviewer_id', '=', rev.id]], ['code', 'version']], { limit: 1, order: 'id desc' });
    check('B13 editor has a draft payment request assigned to the reviewer', !!dossier);
    const versions = [dossier.version];
    const ep = await page(editor);
    const rp = await page(reviewer);
    const openDossier = async p => {
      await p.goto(`${base}/odoo/action-${ACTION.payments}/${dossier.id}`);
      await p.locator('.o_form_view').first().waitFor();
      await settle(p);
    };
    const transition = async (p, button, field, text) => {
      await p.getByRole('button', { name: button, exact: true }).first().click();
      await p.locator('.modal .o_form_view').first().waitFor();
      evidence.chains[`dialog-${button}`] = await p.locator('.modal .o_form_view').first().getAttribute('class');
      if (field) await fillModal(p, field, text);
      await shot(p, `dossier-dialog-${versions.length}-1440`);
      await confirm(p, 'Xác nhận');
      versions.push((await ok(editor, 'tp.payment.request', 'read', [[dossier.id], ['version']]))[0].version);
    };
    await openDossier(ep);
    await transition(ep, 'Gửi rà soát', 'fix_summary', 'KD-UI-003 gửi rà soát');
    await shot(ep, 'dossier-submitted-1440', true);
    await openDossier(rp);
    await transition(rp, 'Trả lại', 'reason', 'KD-UI-003: thiếu chứng từ');
    await openDossier(ep);
    await transition(ep, 'Mở bản sửa', 'reason', 'Bổ sung chứng từ');
    const state = (await ok(editor, 'tp.payment.request', 'read', [[dossier.id], ['state']]))[0].state;
    evidence.chains.dossier = { code: dossier.code, id: dossier.id, versions, state };
    check('B13 dossier submit → return → rework, version +1 each step', state === 'draft' && versions.every((v, i) => !i || v === versions[i - 1] + 1), evidence.chains.dossier);
    check('B13 transition dialog styled', ['Gửi rà soát', 'Trả lại', 'Mở bản sửa'].every(b => (evidence.chains[`dialog-${b}`] || '').includes('tp_kd_form')), evidence.chains);
    await shot(ep, 'dossier-reworked-1440', true);
    await editor.close();
    await reviewer.close();
  });

  // ------------------------------------------------------------ B14 / B15 roles
  await section('roles', async () => {
    const meta = await login(browser, 'metadata');
    let p = await page(meta);
    await openLeaf(p, 'payments');
    let f = await facts(p);
    evidence.roles.metadataList = f.widths;
    let ff;
    check('B14 metadata sees payment rows to open', f.rows > 0, f.rows);
    if (f.rows) {
      await openFirst(p);
      ff = await form(p);
      evidence.roles.metadataForm = ff;
      check('B14 metadata: no money tab and no amount_ids in DOM', !ff.tabs.includes('Giá trị minh họa') && !ff.hasAmountIds, ff.tabs);
      await shot(p, 'form-payments-metadata-1440', true);
    }
    await meta.close();

    const editor = await login(browser, 'editor');
    p = await page(editor);
    const uid = (await ok(editor, 'res.users', 'search_read', [[['login', '=', ctx.actors.editor.login]], ['id']]))[0].id;
    const [inReview] = await ok(editor, 'tp.payment.request', 'search_read', [[['state', '=', 'in_review']], ['id']], { limit: 1 });
    if (inReview) {
      await p.goto(`${base}/odoo/tp.payment.request/${inReview.id}`);
      await p.locator('.o_form_view').first().waitFor();
      await settle(p);
      ff = await form(p);
      check('B14 editor has no "Trả lại"', !ff.buttons.includes('Trả lại'), ff.buttons);
    }
    for (const actor of ['editor', 'reviewer', 'planner', 'metadata']) {
      const context = actor === 'editor' ? editor : await login(browser, actor);
      const lp = await page(context);
      await openLeaf(lp, 'payments');
      f = await facts(lp);
      const count = await ok(context, 'tp.payment.request', 'search_count', [[]]);
      evidence.roles[actor] = { pager: f.pager, total: f.total, search_count: count, uid: actor === 'editor' ? uid : undefined };
      check(`B15 ${actor} pager total = server-scoped count`, Number(f.total || f.rows) === count, evidence.roles[actor]);
      if (actor !== 'editor') await context.close();
    }
    await editor.close();
  });

  // ------------------------------------------------------------ B16 responsive + zoom
  await section('responsive', async () => {
    for (const [w, h] of [[360, 780], [390, 844], [768, 1024], [1280, 900], [1440, 1000], [1920, 1080]]) {
      const context = await login(browser, 'reviewer', { viewport: { width: w, height: h } });
      for (const key of (w === 390 ? ['tasks', 'opportunities', 'payments', 'contracts'] : ['tasks', 'payments'])) {
        const p = await page(context);
        await openLeaf(p, key);
        const f = await facts(p);
        evidence.responsive[`${key}-${w}`] = { docOverflow: f.docOverflow, rendererOverflow: f.rendererOverflow, headTruncated: f.headTruncated };
        check(`B16 ${key}@${w} no page horizontal scroll`, f.docOverflow <= 1, f.docOverflow);
        check(`B2 ${key}@${w} headers not truncated`, f.headTruncated.length === 0, f.headTruncated);
        if (w >= 1280) check(`B2 ${key}@${w} badges read in full`, f.badgeTruncated.length === 0, f.badgeTruncated);
        await shot(p, `list-${key}-${w}`);
        if (f.rows && (key === 'payments' || w === 390)) {
          await openFirst(p);
          const ff = await form(p);
          check(`B16 ${key} form@${w} no page horizontal scroll`, ff.docOverflow <= 1, ff.docOverflow);
          if (w < 768) check(`B16 ${key} form@${w} single column`, ff.groupLefts.length <= 2, ff.groupLefts);
          await shot(p, `form-${key}-${w}`, w > 500);
        }
        await p.close();
      }
      await context.close();
    }
    for (const zoom of [1.25, 1.5]) {
      const context = await login(browser, 'reviewer', { viewport: { width: Math.round(1440 / zoom), height: Math.round(1000 / zoom) }, deviceScaleFactor: zoom });
      const p = await page(context);
      await openLeaf(p, 'tasks');
      const f = await facts(p);
      evidence.responsive[`zoom${zoom * 100}`] = { docOverflow: f.docOverflow, rendererOverflow: f.rendererOverflow };
      check(`B16 zoom ${zoom * 100}% no page horizontal scroll`, f.docOverflow <= 1, f.docOverflow);
      await shot(p, `list-tasks-zoom${zoom * 100}`);
      await context.close();
    }
    // Collapsed sidebar (rail) at 1280.
    const context = await login(browser, 'reviewer', { viewport: { width: 1280, height: 900 } });
    const p = await page(context);
    await openLeaf(p, 'tasks');
    await p.locator('.o_tp_kd_sb_collapse').click();
    await p.waitForTimeout(400);
    const f = await facts(p);
    check('B16 rail sidebar: no page horizontal scroll', f.docOverflow <= 1, f.docOverflow);
    await shot(p, 'list-tasks-rail-1280');
    await p.locator('.o_tp_kd_sb_collapse').click();
    await context.close();
  });

  // ------------------------------------------------------------ B18 no style leak
  await section('leak', async () => {
    const context = await login(browser, 'editor');
    const p = await page(context);
    await p.goto(`${base}/odoo/action-tp_contract.action_tp_contracts`);
    await p.locator('.o_list_view').first().waitFor();
    await settle(p);
    let f = await facts(p);
    evidence.leak.contractsApp = { shell: f.shell, firstCellLine: f.firstCellLine, border: f.border };
    check('B18 TP Contracts app: no KH-KD shell', !f.shell);
    check('B18 TP Contracts app: no KH-KD cell rules', f.firstCellLine !== `1px ${KD_LINE}` && f.border !== `1px ${KD_LINE}`, evidence.leak.contractsApp);
    await shot(p, 'leak-contracts-app-1440');
    const create = p.getByRole('button', { name: 'Tạo nháp hợp đồng', exact: true });
    if (write && await create.count()) {
      await create.click();
      await p.locator('.modal .o_form_view').first().waitFor();
      const sep = await p.evaluate(() => {
        const s = document.querySelector('.modal .o_horizontal_separator');
        // Native Odoo separators are already uppercase. The view carries `tp_kd_form` statically;
        // KH-KD styles only apply under the KH-KD shell, so test the rendered KH-KD-only marks:
        // the 1px KH-KD bottom rule on separators and KH-KD sub-table cell lines.
        const td = document.querySelector('.modal .o_list_renderer td.o_data_cell, .modal .o_list_renderer td.o_list_char');
        return {
          shell: document.body.classList.contains('o_tp_kd_shell'),
          rule: s ? `${getComputedStyle(s).borderBottomWidth} ${getComputedStyle(s).borderBottomColor}` : null,
          td: td ? `${getComputedStyle(td).borderRightWidth} ${getComputedStyle(td).borderRightColor}` : null,
        };
      });
      evidence.leak.contractWizardApp = sep;
      check('B18 TP Contracts wizard outside KH-KD keeps native look', !sep.shell && sep.rule !== `1px ${KD_LINE}` && sep.td !== `1px ${KD_LINE}`, sep);
      await shot(p, 'leak-contract-wizard-app-1440');
      await p.locator('.modal footer button[special="cancel"], .modal .btn-close').first().click();
    }
    for (const [name, url] of [['home', '/odoo'], ['project', '/odoo/action-project.open_view_project_all?view_type=list'], ['crm', '/odoo/action-crm.crm_lead_all_leads?view_type=list']]) {
      const lp = await page(context);
      try {
        await lp.goto(`${base}${url}`);
        await lp.waitForTimeout(1500);
        await settle(lp);
        const res = await lp.evaluate(KD => {
          const td = document.querySelector('.o_list_view .o_data_row td:not(.o_list_record_selector)');
          const sep = document.querySelector('.o_form_view .o_horizontal_separator');
          return { shell: document.body.classList.contains('o_tp_kd_shell'), td: td ? `${getComputedStyle(td).borderRightWidth} ${getComputedStyle(td).borderRightColor}` : null, sepTransform: sep ? getComputedStyle(sep).textTransform : null, kdLine: KD };
        }, KD_LINE);
        evidence.leak[name] = res;
        check(`B18 ${name}: no KH-KD shell or table rules`, !res.shell && res.td !== `1px ${KD_LINE}`, res);
        await shot(lp, `leak-${name}-1440`);
      } catch (error) {
        evidence.leak[name] = `not opened: ${error.message.slice(0, 120)}`;
      }
      await lp.close();
    }
    await context.close();
  });

  // ------------------------------------------------------------ B19 overview tables
  await section('overview', async () => {
    for (const [w, h] of [[1440, 1000], [1600, 900], [390, 844]]) {
      const context = await login(browser, 'reviewer', { viewport: { width: w, height: h } });
      const p = await page(context);
      const response = await p.context().request.post(`${base}/web/action/load`, {
        data: { jsonrpc: '2.0', method: 'call', params: { action_id: 'tp_kd_workspace.action_overview' } },
      });
      const loaded = (await response.json()).result;
      if (!loaded?.id) throw new Error('Cannot resolve Overview action');
      await p.goto(`${base}/odoo/action-${loaded.id}`);
      await p.locator('.o_tp_kd_ov').first().waitFor();
      await settle(p);
      const ov = await p.evaluate(() => {
        const table = document.querySelector('.o_tp_kd_ov .o_tp_kd_table');
        const wrap = table?.closest('.o_tp_kd_table_wrap');
        const td = table?.querySelector('tbody td');
        const th = table?.querySelector('thead th');
        return table && {
          wrap: `${getComputedStyle(wrap).borderTopWidth} ${getComputedStyle(wrap).borderTopColor} ${getComputedStyle(wrap).borderTopLeftRadius}`,
          td: `${getComputedStyle(td).borderRightWidth} ${getComputedStyle(td).borderBottomWidth}`,
          head: getComputedStyle(th).backgroundColor, sticky: getComputedStyle(th).position,
          docOverflow: document.documentElement.scrollWidth - window.innerWidth,
        };
      });
      evidence.overview[w] = ov;
      check(`B19 overview@${w} project table lines`, ov && ov.wrap.startsWith('1px') && ov.td === '1px 1px' && ov.head === KD_HEAD, ov);
      check(`B19 overview@${w} no page horizontal scroll`, ov.docOverflow <= 1, ov.docOverflow);
      await shot(p, `overview-${w}`, w > 500);
      // Mouse wheel / touchpad over the page body must scroll the Overview (Odoo keeps .o_action at
      // overflow:hidden on desktop; the Overview root is that element).
      const kpis = await p.locator('.o_tp_kd_ov .o_tp_kd_kpis').first().boundingBox();
      await p.mouse.move(kpis.x + kpis.width / 2, Math.min(kpis.y + kpis.height / 2, h - 40));
      await p.mouse.wheel(0, 600);
      await p.waitForTimeout(600);
      const wheel = await p.evaluate(() => {
        const el = document.querySelector('.o_tp_kd_ov');
        return { overflowY: getComputedStyle(el).overflowY, top: Math.round(el.scrollTop),
          room: el.scrollHeight - el.clientHeight };
      });
      evidence.overview[`${w}-wheel`] = wheel;
      check(`B19 overview@${w} mouse wheel scrolls`, wheel.overflowY === 'auto' && (wheel.top > 0 || wheel.room <= 0), wheel);
      await p.evaluate(() => { document.querySelector('.o_tp_kd_ov').scrollTop = 0; });
      if (w === 1440) {
        await p.locator('.o_tp_kd_projects thead button').first().click();
        await settle(p);
        check('B19 overview sort', ['ascending', 'descending'].includes(await p.locator('.o_tp_kd_projects thead th').first().getAttribute('aria-sort')));
        const menu = p.locator('.o_tp_kd_row_menu').first();
        if (await menu.count()) {
          await menu.click();
          await p.waitForTimeout(250);
          check('B19 Thao tác menu opens', await p.locator('.o-dropdown--menu').count() > 0);
          await shot(p, 'overview-row-menu-1440');
          await p.keyboard.press('Escape');
        }
        const seg = p.locator('.o_tp_kd_g01 .o_tp_kd_seg_btn').first();
        if (await seg.count()) {
          await seg.click();
          await p.locator('.o_list_view').first().waitFor();
          await settle(p);
          const f = await facts(p);
          check('B19 G01 click-through opens a styled KH-KD list', f.classes.includes('tp_kd_table') && f.shell, f.classes);
        }
      }
      await context.close();
    }
  });

  const bad = errors.filter(e => !/favicon|ResizeObserver/.test(e));
  check('B20 no page/console errors', bad.length === 0, bad.slice(0, 5));
  evidence.failures = failures;
  fs.writeFileSync(path.join(out, 'evidence.json'), JSON.stringify(evidence, null, 2));
  ctx.check(`all checks (${failures.length} failed)`, failures.length === 0, failures);
};
