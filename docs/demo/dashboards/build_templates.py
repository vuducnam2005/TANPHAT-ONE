# ruff: noqa: T201
"""Generate the dashboard templates next to this file (NATIVE-DATA-002, CHG-20261102-008).

Tokens are resolved by the seeder from fixture XML IDs: quoted "__X_IDS__" become JSON arrays,
bare __PID_*__/__CID__ inside formulas/domains become integers. No result value is written into a cell.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
TITLE = {'bold': True, 'fontSize': 18, 'textColor': '#01666B', 'verticalAlign': 'middle'}
NOTE = {'italic': True, 'textColor': '#434343', 'verticalAlign': 'middle', 'wrapping': 'wrap'}
HEAD = {'bold': True, 'fillColor': '#E6F2F3', 'verticalAlign': 'middle'}
SECTION = {'bold': True, 'fontSize': 13, 'textColor': '#01666B', 'verticalAlign': 'bottom'}
TOTAL = {'bold': True}


def pivot(pid, name, model, domain, rows, measures, columns=()):
    return {
        'type': 'ODOO', 'id': pid, 'formulaId': pid, 'name': name, 'model': model,
        'domain': domain, 'context': {}, 'measures': measures,
        'rows': [{'fieldName': f} for f in rows], 'columns': [{'fieldName': f} for f in columns],
        'sortedColumn': None, 'fieldMatching': {},
    }


def count():
    return {'id': '__count', 'fieldName': '__count'}


def total(field):
    return {'id': f'{field}:sum', 'fieldName': field, 'aggregator': 'sum'}


def chart(fid, x, y, w, h, title, model, domain, group_by, measure, stacked=False):
    cid = fid + '-c'
    return {
        'id': fid, 'col': 0, 'row': 0, 'offset': {'x': x, 'y': y}, 'width': w, 'height': h, 'tag': 'carousel',
        'data': {
            'chartDefinitions': {cid: {
                'title': {'text': ''}, 'legendPosition': 'top', 'type': 'bar', 'stacked': stacked, 'humanize': True,
                'dataSource': {'type': 'odoo', 'metaData': {
                    'groupBy': group_by, 'measure': measure, 'order': None, 'resModel': model,
                    'mode': 'bar', 'cumulatedStart': False,
                }, 'searchParams': {
                    'comparison': None, 'context': {}, 'domain': domain, 'groupBy': group_by, 'orderBy': [],
                }},
                'dataSetStyles': {},
            }},
            'title': {'text': title, 'bold': True, 'fontSize': 16, 'color': '#01666B'},
            'items': [{'type': 'chart', 'chartId': cid}],
            'fieldMatching': {},
        },
    }


def spreadsheet(sheet_id, cells, styles, formats, cols, rows, figures, pivots, number_formats, merges):
    style_ids, sheet_styles = {}, {}
    for zone, style in styles.items():
        key = json.dumps(style, sort_keys=True)
        style_ids.setdefault(key, str(len(style_ids) + 1))
        sheet_styles[zone] = int(style_ids[key])
    return {
        'version': '19.3.10',
        'sheets': [{
            'id': sheet_id, 'name': 'Dashboard', 'colNumber': 8, 'rowNumber': 60,
            'rows': {str(k): {'size': v} for k, v in rows.items()},
            'cols': {str(k): {'size': v} for k, v in cols.items()},
            'merges': merges, 'cells': cells, 'styles': sheet_styles, 'formats': formats, 'borders': {},
            'conditionalFormats': [], 'dataValidationRules': [], 'figures': figures, 'tables': [],
            'areGridLinesVisible': False, 'isVisible': True, 'backgroundColor': '#F9FAFB', 'headerGroups': {'ROW': [], 'COL': []}, 'comments': {},
        }],
        'styles': {v: json.loads(k) for k, v in style_ids.items()},
        'formats': number_formats, 'borders': {}, 'revisionId': 'START_REVISION', 'uniqueFigureIds': True,
        'settings': {}, 'pivots': pivots, 'pivotNextId': len(pivots) + 1, 'customTableStyles': {},
        'namedRanges': {}, 'globalFilters': [], 'lists': {}, 'listNextId': 1, 'odooLinkReferences': {},
    }


# Rows 0..9 sum to 284px with the default 23px rows; row 10 is a 400px band holding the charts.
ROWS = {0: 44, 1: 56, 10: 400}
CHART_Y = 292


def coordination():
    domain = [['project_id', 'in', '__PROJECT_IDS__'], ['company_id', '=', '__CID__']]
    projects = [('__PID_CAU__', 'DA-2026-001'), ('__PID_DUONG__', 'DA-2026-002'),
                ('__PID_NUT__', 'DA-2026-003'), ('__PID_VENBIEN__', 'DA-2026-004')]
    cells = {
        'A1': 'Điều phối dự án',
        'A2': 'Bốn dự án mẫu DA-2026-001…004. Số liệu đọc trực tiếp từ Project và Timesheets theo quyền người xem; '
              'dữ liệu giả lập phục vụ trình diễn, không phải kết quả vận hành.',
        'A4': 'Dự án', 'B4': 'Mã dự án', 'C4': 'Số task', 'D4': 'Task hoàn tất', 'E4': 'Giờ làm (giờ)', 'F4': 'Dòng giờ làm',
        'A9': 'Tổng', 'C9': '=SUM(C5:C8)', 'D9': '=SUM(D5:D8)', 'E9': '=SUM(E5:E8)', 'F9': '=SUM(F5:F8)',
        'A12': 'Task theo dự án và giai đoạn', 'A13': '=PIVOT(3)',
        'A24': 'Giờ làm theo phòng ban và nhân sự', 'A25': '=PIVOT(4)',
    }
    for row, (pid, code) in enumerate(projects, start=5):
        cells[f'A{row}'] = f'=PIVOT.HEADER(1,"project_id",{pid})'
        cells[f'B{row}'] = code
        cells[f'C{row}'] = f'=IFERROR(PIVOT.VALUE(1,"__count","project_id",{pid})+0,0)'
        cells[f'D{row}'] = f'=IFERROR(PIVOT.VALUE(1,"__count","project_id",{pid},"state","1_done")+0,0)'
        cells[f'E{row}'] = f'=IFERROR(PIVOT.VALUE(2,"unit_amount:sum","project_id",{pid})+0,0)'
        cells[f'F{row}'] = f'=IFERROR(PIVOT.VALUE(2,"__count","project_id",{pid})+0,0)'
    pivots = {
        '1': pivot('1', 'Task theo dự án và trạng thái', 'project.task', domain, ['project_id'], [count()], ['state']),
        '2': pivot('2', 'Giờ làm theo dự án', 'account.analytic.line', domain, ['project_id'], [total('unit_amount'), count()]),
        '3': pivot('3', 'Task theo dự án và giai đoạn', 'project.task', domain, ['project_id'], [count()], ['stage_id']),
        '4': pivot('4', 'Giờ làm theo phòng ban và nhân sự', 'account.analytic.line', domain,
                   ['department_id', 'employee_id'], [total('unit_amount')]),
    }
    figures = [
        chart('tp-coord-tasks', 0, CHART_Y, 470, 380, 'Task theo dự án và giai đoạn', 'project.task', domain,
              ['project_id', 'stage_id'], '__count', stacked=True),
        chart('tp-coord-hours', 480, CHART_Y, 470, 380, 'Giờ làm theo dự án (giờ)', 'account.analytic.line',
              domain, ['project_id'], 'unit_amount'),
    ]
    styles = {'A1': TITLE, 'A2': NOTE, 'A4:F4': HEAD, 'A9:F9': TOTAL, 'A12': SECTION, 'A24': SECTION}
    return spreadsheet('tp_coordination_dashboard', cells, styles, {'E5:E9': 1},
                       {0: 330, 1: 110, 2: 90, 3: 110, 4: 120, 5: 110}, ROWS, figures, pivots, {'1': '#,##0.00'}, ['A2:F2'])


def finance():
    domain_inv = [['id', 'in', '__INVOICE_IDS__'], ['state', '=', 'draft'], ['company_id', '=', '__CID__']]
    domain_exp = [['id', 'in', '__EXPENSE_IDS__'], ['state', '=', 'draft'], ['company_id', '=', '__CID__']]
    cells = {
        'A1': 'Hóa đơn và chi phí dự kiến',
        'A2': 'Hóa đơn và khoản chi đang ở trạng thái NHÁP: chưa hạch toán, chưa thu hoặc chi tiền; không phải doanh thu kế toán '
              'và không gộp với cơ hội CRM hay giá trị hợp đồng. Dữ liệu giả lập phục vụ trình diễn.',
        'A4': 'Chỉ tiêu (bản nháp)', 'B4': 'Giá trị',
        'A5': 'Số hóa đơn nháp', 'B5': '=IFERROR(PIVOT.VALUE(1,"__count")+0,0)',
        'A6': 'Hóa đơn nháp — chưa thuế (VND)', 'B6': '=IFERROR(PIVOT.VALUE(1,"amount_untaxed:sum")+0,0)',
        'A7': 'Hóa đơn nháp — gồm thuế (VND)', 'B7': '=IFERROR(PIVOT.VALUE(1,"amount_total:sum")+0,0)',
        'A8': 'Số khoản chi nháp', 'B8': '=IFERROR(PIVOT.VALUE(2,"__count")+0,0)',
        'A9': 'Khoản chi nháp — tổng (VND)', 'B9': '=IFERROR(PIVOT.VALUE(2,"total_amount:sum")+0,0)',
        'A12': 'Hóa đơn nháp theo dự án (chưa hạch toán)', 'A13': '=PIVOT(1)',
        'A21': 'Khoản chi nháp theo nhân sự', 'A22': '=PIVOT(2)',
    }
    pivots = {
        '1': pivot('1', 'Hóa đơn nháp theo dự án', 'account.move', domain_inv, ['invoice_origin'],
                   [count(), total('amount_untaxed'), total('amount_total')]),
        '2': pivot('2', 'Khoản chi nháp theo nhân sự', 'hr.expense', domain_exp, ['employee_id', 'name'],
                   [count(), total('total_amount')]),
    }
    figures = [
        chart('tp-fin-invoices', 0, CHART_Y, 470, 380, 'Hóa đơn nháp theo dự án (VND)', 'account.move', domain_inv,
              ['invoice_origin'], 'amount_total'),
        chart('tp-fin-expenses', 480, CHART_Y, 470, 380, 'Khoản chi nháp theo nhân sự (VND)', 'hr.expense', domain_exp,
              ['employee_id'], 'total_amount'),
    ]
    styles = {'A1': TITLE, 'A2': NOTE, 'A4:B4': HEAD, 'A12': SECTION, 'A21': SECTION}
    return spreadsheet('tp_finance_draft_dashboard', cells, styles, {'B6:B7': 1, 'B9': 1},
                       {0: 420, 1: 160, 2: 140, 3: 160, 4: 160}, ROWS, figures, pivots, {'1': '#,##0'}, ['A2:E2'])


def finance_connected():
    result = finance()
    domain = [['id', 'in', '__EXPENSE_IDS__'], ['state', 'in', ['draft', 'submitted', 'approved']],
              ['company_id', '=', '__CID__']]
    sheet = result['sheets'][0]
    sheet['cells'].update({
        'A2': 'Hóa đơn còn nháp; chi phí đang soạn, chờ duyệt hoặc đã duyệt với chứng từ nháp. Chưa hạch toán, '
              'chưa thu/chi tiền; không phải doanh thu kế toán, không cộng với CRM/hợp đồng. Dữ liệu giả lập.',
        'A4': 'Chỉ tiêu theo nguồn', 'A8': 'Số khoản chi trong ba giai đoạn', 'A9': 'Tổng khoản chi (VND)',
        'A21': 'Chi phí theo nhân sự và trạng thái',
        'A30': 'Đang soạn', 'B30': '=IFERROR(PIVOT.VALUE(2,"total_amount:sum","state","draft")+0,0)',
        'A31': 'Chờ duyệt', 'B31': '=IFERROR(PIVOT.VALUE(2,"total_amount:sum","state","submitted")+0,0)',
        'A32': 'Đã duyệt, chờ hoàn trả', 'B32': '=IFERROR(PIVOT.VALUE(2,"total_amount:sum","state","approved")+0,0)',
    })
    result['pivots']['2'] = pivot('2', 'Chi phí theo nhân sự và trạng thái', 'hr.expense', domain,
                                   ['employee_id'], [count(), total('total_amount')], ['state'])
    sheet['figures'][1] = chart('tp-fin-expenses', 480, CHART_Y, 470, 380, 'Chi phí theo trạng thái (VND)',
                                 'hr.expense', domain, ['state'], 'total_amount')
    return result


if __name__ == '__main__':
    for name, builder in (('tp_project_coordination', coordination), ('tp_invoice_expense_draft', finance),
                          ('tp_invoice_expense_connected', finance_connected)):
        (OUT / f'{name}.template.json').write_text(json.dumps(builder(), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print('wrote', name)
