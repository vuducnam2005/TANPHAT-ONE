from uuid import uuid4

from odoo.http import request


def api_response(data, *, pagination=None):
    meta = {'request_id': str(uuid4())}
    if pagination is not None:
        meta['pagination'] = pagination
    return request.make_json_response({'data': data, 'meta': meta}, headers=[('Cache-Control', 'no-store')])


def api_error(code, message, status):
    return request.make_json_response({
        'error': {'code': code, 'message': message, 'details': None},
        'meta': {'request_id': str(uuid4())},
    }, status=status, headers=[('Cache-Control', 'no-store')])
