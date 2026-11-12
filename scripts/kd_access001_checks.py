"""Mutation probes for KD-ACCESS-001; called only on the owned clone, rolled back."""
# ruff: noqa: PLC0415
from uuid import uuid4


def rehearse(env, native, delta):
    from odoo.exceptions import AccessDenied, AccessError, UserError

    from odoo.addons.tp_contract.exceptions import ContractWorkflowError
    checks = []
    users = {a: env['res.users'].browse(r['id']) for a, r in delta['users'].items()}

    def check(name, condition):
        native.require(bool(condition), name)
        checks.append(name)

    def denied(name, fn):
        try:
            with env.cr.savepoint():
                fn()
        except (AccessDenied, AccessError, UserError, ContractWorkflowError):
            checks.append(name)
            return
        raise AssertionError(name + ' unexpectedly allowed')

    def transition(record, action, user, **values):
        record = record.with_user(user)
        result = getattr(record, 'action_' + action)()
        wizard = env['tp.kd.transition'].with_user(user).browse(result['res_id'])
        if values:
            wizard.write(values)
        wizard.action_confirm()
        return wizard

    models = {'allocation': 'tp.allocation', 'production': 'tp.production', 'acceptance': 'tp.acceptance',
              'payment': 'tp.payment.request', 'plan': 'tp.periodic.plan', 'credential': 'tp.credential', 'obligation': 'tp.obligation'}
    made = []
    # Copy only declared business snapshot inputs; never copy owner/history/state/money from existing dossiers.
    for position, (alias, row) in enumerate(delta['users'].items()):
        user, head = users[alias], users['head']
        pid = row['projects'][0]
        project = env['project.project'].browse(pid)
        for domain, model in models.items():
            granted = env['tp.kd.grant']._has(project, domain, 'prepare', user)
            template = env[model].search([('project_id', '=', pid)], limit=1) or env[model].search([], limit=1)
            native.require(template, 'Missing synthetic template for ' + model)
            inputs = ['date', 'date_due', 'period_from', 'period_to', 'contract_id', 'scope'] + list(template._kd_snapshot_fields)
            values = {}
            for name in inputs:
                value = template[name]
                values[name] = value.id if template._fields[name].type == 'many2one' else value
            values.update(code='KD-ACCESS-PROBE-' + uuid4().hex[:12], name='Synthetic access probe',
                          project_id=pid, owner_id=user.id, reviewer_id=head.id)
            if domain == 'plan':
                values.update(period_kind='month', period_from=f'{2050 + position}-01-01', period_to=f'{2050 + position}-01-31', contract_id=False)
            if domain == 'credential':
                values.update(subject_kind='organization')
            if not granted:
                # Keep reviewer different from owner even for denied head preparation.
                values['reviewer_id'] = users['deputy'].id if alias == 'head' else head.id
                denied(alias + ' no prepare ' + domain, lambda m=model, v=values: env[m].with_user(user).create(v))
                continue
            rec = env[model].with_user(user).create(values)
            made.append(rec)
            check(alias + ' prepare ' + domain, rec.owner_id == user)
            denied(alias + ' other owner cannot write ' + domain,
                   lambda r=rec: r.with_user(head).write({'name': 'forged', 'version': r.version}))
            if alias == 'support':
                denied('support cannot submit credential', lambda r=rec: transition(r, 'submit', user))
                continue
            denied(alias + ' forged state ' + domain, lambda r=rec: r.write({'state': 'in_review', 'version': r.version}))
            if rec._kd_money_model:
                amount = {'amount_state': 'confirmed', 'value': 987654321, 'tax_basis': 'excluding_tax'}
                if domain == 'plan':
                    amount['measure'] = 'production'
                rec.write({'amount_ids': [(0, 0, amount)], 'version': rec.version})
                check(alias + ' financial draft ' + domain, rec.amount_ids.value == 987654321)
            transition(rec, 'submit', user)
            check(alias + ' submit ' + domain, rec.state == 'in_review')
            denied(alias + ' self return ' + domain, lambda r=rec: transition(r, 'return', user, reason='no self review'))
            denied(alias + ' other reviewer ' + domain, lambda r=rec: transition(r, 'return', users['deputy'] if alias != 'deputy' else users['planning'], reason='wrong reviewer'))
            denied(alias + ' reason required ' + domain, lambda r=rec: transition(r, 'return', head))
            transition(rec, 'return', head, reason='Synthetic missing scope')
            check(alias + ' head return ' + domain, rec.state == 'returned')
            transition(rec, 'rework', user, reason='Synthetic correction')
            stale = env['tp.kd.transition'].with_user(user).browse(rec.action_submit()['res_id'])
            rec.write({'name': 'Corrected synthetic access probe', 'version': rec.version})
            denied(alias + ' stale version ' + domain, stale.action_confirm)
            transition(rec, 'submit', user, fix_summary='Synthetic correction completed')
            check(alias + ' resubmit ' + domain, rec.state == 'in_review' and len(rec.event_ids) >= 4)
            denied(alias + ' sent delete blocked ' + domain, rec.unlink)
            # Review eligibility is project/domain coarse but return still requires exact reviewer.
            if alias in ['deputy', 'project_lead']:
                # Use a new dossier owned by planning in the overlapping project.
                review_values = values | {'code': 'KD-ACCESS-REVIEW-' + uuid4().hex[:12], 'owner_id': users['planning'].id,
                                          'reviewer_id': user.id}
                if domain in ['allocation', 'production', 'plan', 'credential']:
                    if domain == 'plan':
                        review_values.update(period_from=f'{2060 + position}-01-01', period_to=f'{2060 + position}-01-31')
                    review_rec = env[model].with_user(users['planning']).create(review_values)
                    transition(review_rec, 'submit', users['planning'])
                    transition(review_rec, 'return', user, reason='Assigned lead review')
                    check(alias + ' assigned review ' + domain, review_rec.state == 'returned')

    for alias in ['deputy', 'project_lead']:
        user = users[alias]
        project = env['project.project'].browse(delta['users'][alias]['projects'][0])
        workflow = env['tp.contract.workflow'].with_user(user)
        result = workflow._tp_run('create_contract', {
            'project_id': project.id, 'code': 'KD-ACCESS-CTR-' + uuid4().hex[:10], 'name': 'Synthetic access contract',
            'contract_type': 'owner', 'currency': 'VND', 'lines': [{'scope_key': 'L1', 'name': 'Synthetic scope',
            'amount': {'state': 'confirmed', 'value': '987654321', 'tax_basis': 'excluding_tax'}}]}, key=uuid4().hex)
        contract, revision = result['contract'], result['revision']

        def run(actor, action, **payload):
            return env['tp.contract.workflow'].with_user(actor)._tp_run(action,
                {'expected_version': contract.aggregate_version, **payload}, key=uuid4().hex,
                contract_id=contract.id, revision_id=revision.id)
        check(alias + ' contract draft money', bool(contract))
        denied(alias + ' self contract reviewer', lambda: run(user, 'submit_review', reviewer_id=user.id))
        run(user, 'submit_review', reviewer_id=users['head'].id)
        denied('planning no contract return ' + alias, lambda: run(users['planning'], 'return_review', reason='forged'))
        run(users['head'], 'return_review', reason='Synthetic return', issues=[])
        run(user, 'begin_rework', reason='Synthetic correction')
        run(user, 'submit_review', reviewer_id=users['head'].id, fix_summary='Corrected')
        check(alias + ' contract return rework resubmit', revision.review_state == 'in_review')

    # Expiry/revoke/assignment probes affect only owned clone users, within rollback transaction.
    for kind, model in [('project', 'tp.project.grant'), ('typed', 'tp.kd.grant')]:
        grant = env[model].browse(delta['project_grants' if kind == 'project' else 'kd_grants'][0])
        user, project = grant.user_id, grant.project_id

        def allowed():
            return (env[model].with_user(user)._tp_has_capability(project, grant.capability,
                    project.tp_department_id if grant.capability != 'financial_read' else None) if kind == 'project' else
                    env[model].with_user(user)._has(project, grant.domain, grant.capability))
        check(kind + ' grant starts allowed', allowed())
        grant.date_end = '2000-01-01'
        check(kind + ' expired denied', not allowed())
        grant.date_end = False
        grant.active = False
        check(kind + ' revoked denied', not allowed())
        grant.active = True
    for alias, row in delta['users'].items():
        user = users[alias]
        assignment = env['tp.project.assignment'].search([('id', 'in', delta['assignments']),
                                                        ('user_id', '=', user.id)], limit=1)
        project = assignment.project_id
        assignment.active = False
        env.transaction.invalidate_access_cache()
        actor_project = project.with_user(user)
        check(alias + ' revoked assignment read', not actor_project.has_access('read'))
        check(alias + ' revoked assignment search', not env['project.project'].with_user(user).search([('id', '=', project.id)]))
        denied(alias + ' revoked assignment export', lambda: actor_project.export_data(['name']))
        dashboard = env['tp.kd.overview'].with_user(user).get_kd_dashboard()
        check(alias + ' revoked assignment dropdown', project.id not in [p['id'] for p in dashboard['options']['projects']])
        assignment.active = True
        env.transaction.invalidate_access_cache()
    # Rollback is archive/revoke, never delete existing or new accounts with history.
    for model, key in [('tp.project.grant', 'project_grants'), ('tp.kd.grant', 'kd_grants'),
                       ('tp.project.assignment', 'assignments')]:
        env[model].browse(delta[key]).write({'active': False})
    for user in users.values():
        user.active = False
    check('rollback archives all five users', not any(u.active for u in users.values()))
    check('rollback preserves every old user', env['res.users'].with_context(active_test=False).browse(delta['old_user_ids']).exists().ids == delta['old_user_ids'])
    return checks
