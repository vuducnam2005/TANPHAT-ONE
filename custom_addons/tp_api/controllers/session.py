from odoo.http import Controller, request, route

from odoo.addons.tp_api.services.response import api_response


class TpSession(Controller):
    @route('/api/v1/me', type='http', auth='user', methods=['GET'], readonly=True)
    def me(self):
        user = request.env.user
        return api_response({
            'user': {'id': user.id, 'name': user.name},
            'company': {'id': request.env.company.id, 'name': request.env.company.name},
            'companies': [{'id': company.id, 'name': company.name} for company in request.env.companies],
            'csrf_token': request.csrf_token(),
            'api_version': '1',
        })
