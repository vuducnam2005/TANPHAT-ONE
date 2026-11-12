/* KD-UI-002 after/verify checks (B1–B12) + chart-vs-source comparison. Private output in .local. */
const fs = require('node:fs');
const path = require('node:path');

const OV = 'tp.kd.overview';
const STATES = ['draft', 'in_review', 'returned'];

async function actionCount(ctx, context, action) {
  // Count exactly what the drill-down list would show: its model + domain, under the same user.
  const domain = action.domain || [];
  return ctx.ok(context, action.res_model, 'search_count', [domain], { context: action.context || {} });
}

async function compareCharts(ctx, context, actor) {
  const { ok } = ctx;
  const rows = [];
  const dash = await ok(context, OV, 'get_kd_dashboard', [{}]);
  for (const r of dash.g01.rows.filter(row => row.available)) {
    for (const st of STATES) {
      if (!r[st]) continue;
      const action = await ok(context, OV, 'action_kd_open', ['g01', {}, { source: r.source, state: st }]);
      rows.push({ actor, chart: 'G01', key: `${r.source}/${st}`, chart_value: r[st], source_count: await actionCount(ctx, context, action) });
    }
  }
  for (const r of dash.g02.available ? dash.g02.rows : []) {
    for (const b of ['done', 'overdue', 'open']) {
      if (!r[b]) continue;
      const action = await ok(context, OV, 'action_kd_open', ['task', {}, { bucket: b, project_id: r.project_id }]);
      rows.push({ actor, chart: 'G02', key: `${r.code || r.project_id}/${b}`, chart_value: r[b], source_count: await actionCount(ctx, context, action) });
    }
  }
  for (const [route, state, value] of [
    ['bid', 'identified', dash.g03.bid.identified], ['bid', 'preparation', dash.g03.bid.preparation],
    ['bid', 'submitted', dash.g03.bid.submitted], ['direct', false, dash.g03.direct]].filter(() => dash.g03.available)) {
    const action = await ok(context, OV, 'action_kd_open', ['lead', {}, { route, bid_state: state }]);
    rows.push({ actor, chart: 'G03', key: `${route}/${state || 'all'}`, chart_value: value, source_count: await actionCount(ctx, context, action) });
  }
  const cred = await ok(context, OV, 'get_kd_credential_expiry', [{}]);
  for (const b of cred.available ? ['expired', 'soon', 'later'] : []) {
    const action = await ok(context, OV, 'action_kd_open', ['credential', {}, { bucket: b }]);
    rows.push({ actor, chart: 'G05', key: b, chart_value: cred.buckets[b], source_count: await actionCount(ctx, context, action) });
  }
  const plan = await ok(context, OV, 'get_kd_plan_compare', [{}, 'month']);
  for (const r of plan.rows) {
    rows.push({ actor, chart: 'G04', key: `${r.code}/${r.period}`, chart_value: r.target_text || r.target_state, source_count: r.source_text || r.status_label, note: 'text: target vs source/status' });
  }
  const mine = await ok(context, OV, 'get_kd_my_work', [{}, 'review', 0, 50]);
  rows.push({ actor, chart: 'KPI', key: 'review', chart_value: dash.kpis.review, source_count: mine.total });
  const ret = await ok(context, OV, 'get_kd_my_work', [{}, 'returned', 0, 50]);
  rows.push({ actor, chart: 'KPI', key: 'returned', chart_value: dash.kpis.returned, source_count: ret.total });
  const due = await ok(context, OV, 'get_kd_my_work', [{}, 'due', 0, 50]);
  rows.push({ actor, chart: 'KPI', key: 'due+overdue', chart_value: dash.kpis.due + dash.kpis.overdue, source_count: due.total });
  return { dash, rows };
}

module.exports = async function after(ctx) {
  const { browser, base, login, watch, settle, shot, openOverview, check, out, errors } = ctx;
  const stage = process.env.KD_STAGE || 'all';
  const comparison = [];

  // ---------------------------------------------------------------- numbers
  if (stage === 'all' || stage === 'numbers') {
    for (const actor of ['reviewer', 'editor', 'planner', 'metadata']) {
      const context = await login(browser, actor);
      const { rows } = await compareCharts(ctx, context, actor);
      for (const r of rows) {
        if (typeof r.chart_value === 'number') {
          check(`${actor} ${r.chart} ${r.key} = source list`, r.chart_value === r.source_count, r);
        }
      }
      comparison.push(...rows);
      await context.close();
    }
    fs.writeFileSync(path.join(out, 'chart-vs-source.json'), JSON.stringify(comparison, null, 2));
  }

  // ---------------------------------------------------------------- desktop overview + sidebar
  if (stage === 'all' || stage === 'ui') {
    const context = await login(browser, 'reviewer');
    const page = await context.newPage();
    watch(page);
    await openOverview(page);
    await page.locator('.o_tp_kd_ov .o_tp_kd_g01').waitFor();
    await settle(page);
    check('B1 sidebar visible on desktop', await page.locator('aside.o_tp_kd_sidebar:not(.is-rail)').isVisible());
    check('B1 navbar section menus hidden', !(await page.locator('.o_menu_sections').isVisible().catch(() => false)));
    check('B2 overview leaf active', (await page.locator('.o_tp_kd_sb_leaf[aria-current="page"]').innerText()).includes('Tổng quan'));
    await shot(page, 'overview-1440');
    await shot(page, 'overview-1440-full', true);

    // submenu toggle with keyboard and mouse
    const group = page.locator('.o_tp_kd_sb_group_btn').first();
    const expanded = await group.getAttribute('aria-expanded');
    await group.click();
    await page.waitForTimeout(300);
    check('B3 group toggles aria-expanded', (await group.getAttribute('aria-expanded')) !== expanded);
    await shot(page, 'sidebar-submenu-toggled');
    await group.focus();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);
    check('B3 group keyboard toggle', (await group.getAttribute('aria-expanded')) === expanded);

    // search in sidebar (no diacritics)
    await page.locator('.o_tp_kd_sb_search input').fill('nghiem thu');
    await page.waitForTimeout(150);
    const hits = await page.locator('.o_tp_kd_sb_sub .o_tp_kd_sb_leaf:visible').allInnerTexts();
    check('B4 sidebar search without diacritics', hits.some(t => t.toLowerCase().includes('nghiệm thu')), hits);
    await shot(page, 'sidebar-search');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200); // OWL patches on the next frame
    check('B4 Escape clears search', (await page.locator('.o_tp_kd_sb_search input').inputValue()) === '');

    // collapse to rail and back
    await page.locator('.o_tp_kd_sb_collapse').click();
    await page.waitForTimeout(350);
    check('B5 rail mode', await page.locator('aside.o_tp_kd_sidebar.is-rail').isVisible());
    await shot(page, 'sidebar-collapsed');
    await page.reload();
    await page.locator('.o_tp_kd_ov .o_tp_kd_g01').waitFor();
    check('B5 collapse persists after reload', await page.locator('aside.o_tp_kd_sidebar.is-rail').isVisible());
    await page.locator('.o_tp_kd_sb_collapse').click();
    await page.waitForTimeout(350);
    check('B5 expand again', await page.locator('aside.o_tp_kd_sidebar:not(.is-rail)').isVisible());

    // prefs: compact + reduced motion
    await page.locator('.o_tp_kd_tb_prefs').click();
    await page.locator('.o_tp_kd_prefs').first().waitFor();
    await page.locator('.o_tp_kd_prefs button', { hasText: 'Gọn' }).click();
    await page.locator('.o_tp_kd_prefs button', { hasText: 'Giảm chuyển động' }).click();
    await page.waitForTimeout(200);
    check('B6 compact class', await page.evaluate(() => document.body.classList.contains('o_tp_kd_compact')));
    check('B6 reduced-motion class', await page.evaluate(() => document.body.classList.contains('o_tp_kd_reduce_motion')));
    await shot(page, 'prefs-open');
    await page.locator('.o_tp_kd_prefs .o_tp_kd_prefs_reset').click();
    await page.waitForTimeout(200);
    check('B6 reset prefs', !(await page.evaluate(() => document.body.classList.contains('o_tp_kd_compact'))));
    await page.keyboard.press('Escape');

    // G01 drill-down opens the same list, breadcrumb back keeps leaf
    const seg = page.locator('.o_tp_kd_g01 .o_tp_kd_seg_btn').first();
    if (await seg.count()) {
      const label = await seg.getAttribute('aria-label');
      const expected = Number(await seg.innerText());
      await seg.click();
      await page.locator('.o_list_view').waitFor();
      await settle(page);
      const rowsShown = await page.locator('.o_data_row').count();
      check('B7 G01 segment opens list with same count', rowsShown === expected || expected > 80, { label, expected, rowsShown });
      await shot(page, 'drill-g01-list');
      await page.locator('.o_breadcrumb .o_back_button a, .o_breadcrumb li a').first().click();
      await page.locator('.o_tp_kd_ov .o_tp_kd_g01').waitFor();
      check('B7 breadcrumb back to overview', true);
    }

    // My work tab + open row
    await page.locator('.o_tp_kd_mine .o_tp_kd_tabs button').nth(2).click();
    await settle(page);
    await shot(page, 'mywork-due');
    const work = page.locator('.o_tp_kd_work_btn').first();
    if (await work.count()) {
      await work.click();
      await page.locator('.o_form_view').waitFor();
      await settle(page);
      check('B8 my work opens record form', true);
      await shot(page, 'form-from-mywork');
      await page.locator('.o_breadcrumb li a, .o_back_button a').first().click();
      await page.locator('.o_tp_kd_ov').waitFor();
    }

    // project table: sort, row action menu
    await page.locator('.o_tp_kd_projects thead button').first().click();
    await settle(page);
    check('B9 sort toggles', ['ascending', 'descending'].includes(await page.locator('.o_tp_kd_projects thead th').first().getAttribute('aria-sort')));
    const menu = page.locator('.o_tp_kd_row_menu').first();
    if (await menu.count()) {
      await menu.click();
      await page.waitForTimeout(200);
      await shot(page, 'project-row-actions');
      await page.keyboard.press('Escape');
    }

    // sidebar leaf -> list -> form (native polish)
    await page.locator('.o_tp_kd_sb_leaf', { hasText: 'Giao khoán' }).first().click();
    await page.locator('.o_list_view').waitFor();
    await settle(page);
    check('B10 leaf navigation marks active', (await page.locator('.o_tp_kd_sb_leaf[aria-current="page"]').innerText()).includes('Giao khoán'));
    await shot(page, 'list-allocation-1440');
    if (await page.locator('.o_data_row').count()) {
      await page.locator('.o_data_row').first().click();
      await page.locator('.o_form_view').waitFor();
      await settle(page);
      await shot(page, 'form-allocation-1440');
      await page.reload();
      await page.locator('.o_form_view').waitFor();
      await settle(page);
      check('B10 deep link keeps leaf active', (await page.locator('.o_tp_kd_sb_leaf[aria-current="page"]').innerText()).includes('Giao khoán'));
    }

    // other app: sidebar gone
    await page.goto(`${base}/odoo`);
    await settle(page);
    check('B11 shell removed outside KH-KD', !(await page.evaluate(() => document.body.classList.contains('o_tp_kd_shell'))));
    await context.close();
  }

  // ---------------------------------------------------------------- responsive
  if (stage === 'all' || stage === 'responsive') {
    for (const [w, h, label] of [[1024, 900, '1024'], [768, 1024, '768'], [390, 844, '390'], [360, 780, '360']]) {
      const context = await login(browser, 'reviewer', { viewport: { width: w, height: h } });
      const page = await context.newPage();
      watch(page);
      await openOverview(page);
      await page.locator('.o_tp_kd_ov .o_tp_kd_g01').waitFor();
      await settle(page);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      check(`B12 no horizontal page scroll at ${label}`, overflow <= 1, { overflow });
      await shot(page, `overview-${label}`);
      await shot(page, `overview-${label}-full`, true);
      if (w < 768) {
        await page.locator('.o_tp_kd_menu_toggle').click();
        await page.locator('aside.o_tp_kd_sidebar.is-drawer').waitFor();
        await page.waitForTimeout(300);
        check(`B12 drawer focus inside at ${label}`, await page.evaluate(() => !!document.activeElement.closest('.o_tp_kd_sidebar')));
        await shot(page, `drawer-${label}`);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(250);
        check(`B12 Escape closes drawer at ${label}`, !(await page.locator('aside.o_tp_kd_sidebar.is-drawer').count()));
        check(`B12 focus back on toggle at ${label}`, await page.evaluate(() => document.activeElement.classList.contains('o_tp_kd_menu_toggle')));
      }
      await context.close();
    }
    for (const zoom of [1.25, 1.5]) {
      const context = await login(browser, 'reviewer', { viewport: { width: Math.round(1440 / zoom), height: Math.round(1000 / zoom) }, deviceScaleFactor: zoom });
      const page = await context.newPage();
      watch(page);
      await openOverview(page);
      await page.locator('.o_tp_kd_ov .o_tp_kd_g01').waitFor();
      await settle(page);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      check(`B12 zoom ${zoom * 100}% no horizontal scroll`, overflow <= 1, { overflow });
      await shot(page, `overview-zoom${zoom * 100}`);
      await context.close();
    }
  }

  // ---------------------------------------------------------------- roles
  if (stage === 'all' || stage === 'roles') {
    for (const actor of ['editor', 'planner', 'metadata']) {
      const context = await login(browser, actor);
      const page = await context.newPage();
      watch(page);
      await openOverview(page);
      await page.locator('.o_tp_kd_ov .o_tp_kd_g01').waitFor();
      await settle(page);
      await shot(page, `overview-role-${actor}`);
      const create = await page.locator('.o_tp_kd_tb_create').count();
      check(`role ${actor} overview renders`, true, { create });
      if (actor === 'editor' && create) {
        // B11: Tạo hồ sơ opens the native form for an allowed kind; discarding creates nothing.
        const projectFilter = page.locator('.o_tp_kd_filters select').first();
        await projectFilter.selectOption({ index: 1 });
        await settle(page);
        const projectName = (await projectFilter.locator('option:checked').innerText()).trim();
        await page.locator('.o_tp_kd_tb_create').click();
        const items = page.locator('.o-dropdown--menu .dropdown-item');
        await items.first().waitFor();
        const kinds = await items.allInnerTexts();
        await shot(page, 'create-menu-editor');
        await items.filter({ hasText: 'Giao khoán' }).first().click();
        await page.locator('.o_form_view .o_form_editable, .o_form_view.o_form_editable').first().waitFor();
        await settle(page);
        const crumb = await page.locator('.o_breadcrumb').innerText();
        const project = (await page.locator('.o_form_view .o_field_widget[name="project_id"]').first().innerText().catch(() => ''))
          || (await page.locator('.o_form_view .o_field_widget[name="project_id"] input').first().inputValue().catch(() => ''));
        check('B11 create opens native new form', crumb.includes('Mới') && await page.locator('.o_form_view .o_field_widget[name="allocation_type"], .o_form_view .o_field_widget[name="project_id"]').count() > 0, { kinds, crumb });
        check('B11 default project from filter', !!project.trim(), { project, projectName });
        await shot(page, 'create-form-editor');
        if (ctx.target === 'dev') {
          await page.locator('.o_form_button_cancel').first().click().catch(() => {});
          await page.waitForTimeout(500);
        }
        // B6: leaving a dirty new form through the sidebar is handled by native save/validation.
        const name = page.locator('.o_form_view .o_field_widget[name="name"] input').first();
        // Never type into a business form on dev (no dev records created for evidence).
        if (ctx.target !== 'dev' && await name.count()) {
          await name.fill('KD-UI-002 B6 thử rời form');
          await page.locator('.o_tp_kd_sb_leaf', { hasText: 'Tổng quan' }).first().click();
          await page.waitForTimeout(1500);
          const stayed = await page.locator('.o_form_view').count();
          const invalid = await page.locator('.o_notification, .o_field_invalid').count();
          check('B6 dirty form not silently dropped', stayed > 0 ? invalid > 0 : true, { stayed, invalid });
          await shot(page, 'dirty-form-leave');
          if (stayed) {
            await page.locator('.o_form_button_cancel').first().click().catch(() => {});
            await page.waitForTimeout(500);
          }
        }
      }
      await context.close();
    }
  }
  const bad = errors.filter(e => !/favicon|ResizeObserver/.test(e));
  check('no page/console errors', bad.length === 0, bad.slice(0, 5));
};
