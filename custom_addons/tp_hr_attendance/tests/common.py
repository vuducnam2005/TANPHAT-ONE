"""Synthetic machine-report workbooks and records for HR-ATTENDANCE-001 tests (no real names or hours)."""
import base64
from datetime import timedelta
from io import BytesIO

from openpyxl import Workbook

from odoo import Command
from odoo.tests import TransactionCase

from odoo.addons.tp_organization.models.hr_employee import _ROSTER_WRITE

WEEKDAY = ('T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN')


def report(people, start, days, sheets=('Tuần 1',)):
    """Build an .xlsx like the machine export: period line, STT/Mã/Tên/ID header, Vào/Ra row pairs.

    ``people`` = [{'code': '9001', 'name': 'Synthetic A', 'times': [('07:37', '17:05'), (None, None)]}].
    """
    book = Workbook()
    book.remove(book.active)
    end = start + timedelta(days=days - 1)
    for title in sheets:
        sheet = book.create_sheet(title)
        sheet['A1'] = 'BÁO CÁO CHẤM CÔNG (synthetic)'
        sheet['A3'] = f'Từ ngày {start:%d/%m/%Y} đến ngày {end:%d/%m/%Y}'
        headers = ['STT', 'Mã nhân viên', 'Tên nhân viên', 'ID', 'Chức vụ', '']
        for column, value in enumerate(headers, 1):
            sheet.cell(6, column, value)
        for offset in range(days):
            day = start + timedelta(days=offset)
            sheet.cell(6, 7 + offset, day.day)
            sheet.cell(7, 7 + offset, WEEKDAY[day.weekday()])
        sheet.cell(8, 1, 'PHÒNG SYNTHETIC')
        row = 9
        for index, person in enumerate(people, 1):
            sheet.cell(row, 1, index)
            sheet.cell(row, 2, person.get('source', ''))
            sheet.cell(row, 3, person['name'])
            sheet.cell(row, 4, int(person['code']) if person.get('code') else None)
            sheet.cell(row, 5, 'Nhân viên')
            sheet.cell(row, 6, 'Vào')
            sheet.cell(row + 1, 6, 'Ra')
            for offset, (clock_in, clock_out) in enumerate(person['times']):
                if clock_in:
                    sheet.cell(row, 7 + offset, clock_in)
                if clock_out:
                    sheet.cell(row + 1, 7 + offset, clock_out)
            row += 2
    buffer = BytesIO()
    book.save(buffer)
    return buffer.getvalue()


class AttendanceCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic Attendance Company'})
        cls.dept = cls.env['hr.department'].create({'name': 'Synthetic Attendance Dept', 'company_id': cls.company.id})
        cls.dept_other = cls.env['hr.department'].create({'name': 'Synthetic Attendance Other', 'company_id': cls.company.id})

        def user(login, *groups):
            return cls.env['res.users'].create({
                'name': login, 'login': login, 'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
                'group_ids': [Command.set([cls.env.ref(group).id for group in groups])],
            })

        cls.viewer = user('att001.synthetic.viewer', 'base.group_user')
        cls.colleague = user('att001.synthetic.colleague', 'base.group_user')
        cls.officer = user('att001.synthetic.officer', 'base.group_user')
        cls.manager = user('att001.synthetic.manager', 'hr.group_hr_manager')
        # Source codes are written only through the reviewed roster path (tp_organization guard).
        Employee = cls.env['hr.employee'].with_company(cls.company).with_context(_tp_roster_write=_ROSTER_WRITE)
        cls.emp_a = Employee.create({'name': 'Synthetic Người Một', 'company_id': cls.company.id, 'department_id': cls.dept.id,
                                     'tp_source_code': '9901', 'tp_employee_code': 'TP19901', 'user_id': cls.viewer.id})
        cls.emp_b = Employee.create({'name': 'Synthetic Người Hai', 'company_id': cls.company.id, 'department_id': cls.dept_other.id,
                                     'tp_source_code': '9902', 'tp_employee_code': 'TP19902', 'user_id': cls.colleague.id})

    def env_for(self, user):
        return self.env(user=user, context=dict(self.env.context, allowed_company_ids=[self.company.id]))

    def batch(self, data, user=None, name='Synthetic batch'):
        env = self.env_for(user or self.manager)
        return env['tp.hr.attendance.batch'].create({
            'name': name, 'company_id': self.company.id, 'file_data': base64.b64encode(data).decode(), 'file_name': 'synthetic.xlsx'})

    def run_batch(self, data, user=None, apply=True):
        batch = self.batch(data, user)
        batch.action_preview()
        if apply:
            batch.action_apply()
        return batch

    def lines(self, batch, **filters):
        lines = batch.sudo().line_ids
        for key, value in filters.items():
            lines = lines.filtered(lambda line, key=key, value=value: line[key] == value)
        return lines

    def day(self, employee, work_date):
        return self.env['tp.hr.attendance.day'].sudo().search([('employee_id', '=', employee.id), ('work_date', '=', work_date)])
