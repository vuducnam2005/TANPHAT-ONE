import unicodedata
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/workspace/docker.odoo.conf', '-d', 'tp_tanphat_dev'])
registry = Registry('tp_tanphat_dev')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    Mapping = env['tp.hr.attendance.enti.mapping'].sudo()
    EntiDay = env['tp.hr.attendance.enti.day'].sudo()
    Day = env['tp.hr.attendance.day'].sudo()
    Session = env['tp.hr.attendance.session'].sudo()
    Source = env['tp.hr.attendance.source'].sudo()
    
    source = Source.search([('kind', '=', 'enti_api')], limit=1)
    print(f"=== ENTI SOURCE: ID={source.id}, name='{source.name}', state='{source.state}' ===", flush=True)
    
    # 1. Re-match all mappings
    mappings = Mapping.search([('source_id', '=', source.id)])
    print(f"\nProcessing {len(mappings)} mappings...", flush=True)
    mapped_count = 0
    unmapped_count = 0
    
    for m in mappings:
        m._match_and_apply()
        if m.state == 'mapped':
            mapped_count += 1
        else:
            unmapped_count += 1
            print(f"  Unmapped: [{m.ma_nv}] '{m.ten_nv}' -> reason: {m.match_reason}", flush=True)
            
    print(f"\n-> Mapping complete: {mapped_count} MAPPED, {unmapped_count} UNMAPPED.", flush=True)
    
    # 2. Project all stored enti_days for mapped employees
    enti_days = EntiDay.search([('source_id', '=', source.id)])
    print(f"\nProjecting {len(enti_days)} ENTI daily records to canonical attendance...", flush=True)
    
    applied = 0
    pending = 0
    for ed in enti_days:
        # link employee if mapping is mapped
        mapping = Mapping.search([('source_id', '=', source.id), ('key_nv', '=', ed.key_nv)], limit=1)
        if mapping and mapping.state == 'mapped' and mapping.employee_id:
            ed.sudo().write({'employee_id': mapping.employee_id.id})
            ed._tp_project_to_canonical()
            applied += 1
        else:
            ed.sudo().write({'state': 'pending_map'})
            pending += 1
            
    print(f"-> Projection complete: {applied} APPLIED to canonical, {pending} PENDING mapping.", flush=True)
    
    # 3. Verify canonical records
    total_canonical_days = Day.search_count([('source_kind', '=', 'enti')])
    total_canonical_sessions = Session.search_count([('source', '=', 'enti')])
    print(f"\n=== VERIFICATION ===", flush=True)
    print(f"Total canonical days (source_kind='enti'): {total_canonical_days}", flush=True)
    print(f"Total canonical sessions (source='enti'): {total_canonical_sessions}", flush=True)
    
    # Check sample days
    sample_emps = env['hr.employee'].search([('name', 'in', ['Vũ Đức Nam', 'Trần Phương Đông', 'Lê Nguyên Tuấn'])])
    for emp in sample_emps:
        emp_days = Day.search([('employee_id', '=', emp.id), ('source_kind', '=', 'enti')], order='work_date desc', limit=5)
        print(f"\nSample days for {emp.name} ({emp.tp_employee_code}):", flush=True)
        for d in emp_days:
            print(f"  {d.work_date} ({d.weekday}): in={d.in_time}, out={d.out_time}, hours={d.recorded_hours}, units={d.units}, data_state={d.data_state}", flush=True)
            
    # Commit changes
    cr.commit()
    print("\nDATABASE TRANSACTION COMMITTED SUCCESSFULLY!", flush=True)
