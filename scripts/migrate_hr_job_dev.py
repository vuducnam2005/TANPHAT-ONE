import sys
sys.path.insert(0, '.')
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '.local/odoo.conf'])
registry = Registry('tp_tanphat_dev')

JOB_DEFINITIONS = [
    {'name': 'Chủ tịch', 'sequence': 10},
    {'name': 'Tổng giám đốc', 'sequence': 20},
    {'name': 'Phó Tổng giám đốc', 'sequence': 30},
    {'name': 'Giám đốc', 'sequence': 40},
    {'name': 'Trưởng phòng', 'sequence': 50},
    {'name': 'Phó phòng', 'sequence': 60},
    {'name': 'Kế toán trưởng', 'sequence': 70},
    {'name': 'Kế toán viên', 'sequence': 80},
    {'name': 'Nhân viên', 'sequence': 90},
    {'name': 'Thử việc', 'sequence': 100},
    {'name': 'Lái xe', 'sequence': 110},
]

TITLE_TO_JOB = {
    'Chủ tịch': 'Chủ tịch',
    'Tổng giám đốc': 'Tổng giám đốc',
    'Phó TGĐ': 'Phó Tổng giám đốc',
    'Phó Giám đốc': 'Phó Tổng giám đốc',
    'Giám đốc': 'Giám đốc',
    'Trưởng phòng': 'Trưởng phòng',
    'Trường phòng': 'Trưởng phòng',
    'Phó phòng': 'Phó phòng',
    'Kế toán trưởng': 'Kế toán trưởng',
    'Kế toán trường': 'Kế toán trưởng',
    'Kế toán viên': 'Kế toán viên',
    'Nhân viên': 'Nhân viên',
    'Thử việc': 'Thử việc',
    'Lái xe': 'Lái xe',
}

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    Job = env['hr.job']
    Employee = env['hr.employee']
    company = env['res.company'].search([], limit=1)

    jobs = {}
    for defn in JOB_DEFINITIONS:
        job = Job.search([('name', '=', defn['name']), ('company_id', '=', company.id)], limit=1)
        if not job:
            job = Job.create({
                'name': defn['name'],
                'sequence': defn['sequence'],
                'company_id': company.id,
            })
            print(f'Created job: {job.name} (id={job.id})')
        else:
            job.write({'sequence': defn['sequence']})
            print(f'Existing job: {job.name} (id={job.id})')
        jobs[defn['name']] = job

    # Map all employees
    employees = Employee.search([])
    mapped_count = 0
    for emp in employees:
        source_title = (emp.tp_source_title or '').strip()
        target_name = TITLE_TO_JOB.get(source_title)
        if target_name and target_name in jobs:
            emp.write({'job_id': jobs[target_name].id})
            mapped_count += 1
            print(f'Mapped {emp.tp_employee_code} ({emp.name}): {source_title} -> {target_name}')
        else:
            print(f'WARNING: Unmapped {emp.tp_employee_code} ({emp.name}): {source_title}')

    cr.commit()
    print(f'Total employees: {len(employees)}, Successfully mapped: {mapped_count}')
