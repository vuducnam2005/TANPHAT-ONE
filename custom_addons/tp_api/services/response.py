from uuid import uuid4

from odoo.http import request


def api_response(data, *, pagination=None, status=200, headers=None, request_id=None):
    meta = {'request_id': request_id or str(uuid4())}
    if pagination is not None:
        meta['pagination'] = pagination
    return request.make_json_response(
        {'data': data, 'meta': meta}, status=status, headers=[('Cache-Control', 'no-store'), *(headers or [])],
    )


def api_error(code, message, status, details=None):
    return request.make_json_response({
        'error': {'code': code, 'message': message, 'details': details},
        'meta': {'request_id': str(uuid4())},
    }, status=status, headers=[('Cache-Control', 'no-store')])
