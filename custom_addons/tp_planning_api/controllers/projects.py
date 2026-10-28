from werkzeug.exceptions import NotFound

from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain
from odoo.http import Controller, request, route

from odoo.addons.tp_api.services.response import api_response


def _require_reader():
    if not request.env.user.has_group('tp_core.group_user'):
        message = request.env._('Tan Phat platform membership is required.')
        raise AccessError(message)


def _project_dto(project):
    return {
        'id': project.id,
        'code': project.tp_code,
        'name': project.name,
        'active': project.active,
        'company': {'id': project.company_id.id, 'name': project.company_id.name},
        'department': {'id': project.tp_department_id.id, 'name': project.tp_department_id.name} if project.tp_department_id else None,
        'customer': {'id': project.partner_id.id, 'name': project.partner_id.name} if project.partner_id else None,
        'updated_at': project.write_date.isoformat(timespec='seconds') + 'Z',
    }


class TpProjects(Controller):
    @route('/api/v1/projects', type='http', auth='user', methods=['GET'], readonly=True)
    def projects(self, **params):
        _require_reader()
        if set(params) - {'limit', 'offset', 'q'}:
            message = request.env._('Unsupported query parameter.')
            raise ValidationError(message)
        try:
            limit = int(params.get('limit', 20))
            offset = int(params.get('offset', 0))
        except (ValueError, TypeError) as error:
            message = request.env._('Limit and offset must be integers.')
            raise ValidationError(message) from error
        if not 1 <= limit <= 100 or not 0 <= offset <= 10000:
            message = request.env._('Limit must be 1-100 and offset must be 0-10000.')
            raise ValidationError(message)
        query = params.get('q', '').strip()
        if len(query) > 100:
            message = request.env._('The search query is too long.')
            raise ValidationError(message)
        domain = Domain('tp_managed', '=', True)
        if query:
            domain &= Domain('name', 'ilike', query) | Domain('tp_code', 'ilike', query)
        projects = request.env['project.project'].search(domain, limit=limit + 1, offset=offset, order='tp_code, id')
        return api_response([_project_dto(project) for project in projects[:limit]], pagination={
            'limit': limit, 'offset': offset, 'has_more': len(projects) > limit,
        })

    @route('/api/v1/projects/<int:project_id>', type='http', auth='user', methods=['GET'], readonly=True)
    def project(self, project_id, **params):
        _require_reader()
        if params:
            message = request.env._('Unsupported query parameter.')
            raise ValidationError(message)
        project = request.env['project.project'].search(Domain('id', '=', project_id) & Domain('tp_managed', '=', True), limit=1)
        if not project:
            message = request.env._('The requested project was not found.')
            raise NotFound(message)
        return api_response(_project_dto(project))
