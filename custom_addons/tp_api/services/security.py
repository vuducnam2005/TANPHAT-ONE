from urllib.parse import urlsplit

from odoo.http import request

from .errors import ApiProblem


def require_write_protection():
    """Check the browser write guard of a JSON write route and return its body.

    Write routes declare ``csrf=False`` because Odoo reads the CSRF token only
    from form parameters; this check replaces it. A request must come from the
    same site (Fetch Metadata, else Origin against Host), carry the session
    bound token from ``GET /api/v1/me`` in ``X-CSRF-Token`` and send a JSON
    object body.
    """
    headers = request.httprequest.headers
    fetch_site = headers.get('Sec-Fetch-Site')
    if fetch_site is not None and fetch_site != 'same-origin':
        raise ApiProblem(403, 'cross_origin', 'Cross-site write requests are not accepted.')
    origin = headers.get('Origin')
    # httprequest.host follows X-Forwarded-Host only when Odoo runs in proxy mode.
    if origin is not None and urlsplit(origin).netloc != request.httprequest.host:
        raise ApiProblem(403, 'cross_origin', 'Cross-site write requests are not accepted.')
    if not request.validate_csrf(headers.get('X-CSRF-Token')):
        raise ApiProblem(403, 'csrf_invalid', 'The CSRF token is missing or expired. Reload and try again.')
    if request.httprequest.mimetype != 'application/json':
        raise ApiProblem(415, 'unsupported_media_type', 'Send the request body as application/json.')
    try:
        body = request.get_json_data()
    except ValueError as error:
        raise ApiProblem(400, 'invalid_request', 'The request body is not valid JSON.') from error
    if not isinstance(body, dict):
        raise ApiProblem(400, 'invalid_request', 'The request body must be a JSON object.')
    return body
