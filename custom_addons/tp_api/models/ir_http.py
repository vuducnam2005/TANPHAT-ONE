import logging

from werkzeug.exceptions import HTTPException

from odoo import models
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import request
from odoo.http.session import SessionExpiredException

from odoo.addons.tp_api.services.response import api_error

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _handle_error(cls, exception):
        if not request.httprequest.path.startswith('/api/v1/'):
            return super()._handle_error(exception)
        if isinstance(exception, (SessionExpiredException, AccessDenied)):
            return api_error('unauthenticated', 'Please sign in to continue.', 401)
        if isinstance(exception, AccessError):
            return api_error('forbidden', 'You do not have permission for this operation.', 403)
        if isinstance(exception, MissingError):
            return api_error('not_found', 'The requested record was not found.', 404)
        if isinstance(exception, (ValidationError, UserError)):
            return api_error('invalid_request', str(exception), 400)
        if isinstance(exception, HTTPException) and exception.code and exception.code < 500:
            return api_error(exception.name.lower().replace(' ', '_'), exception.description, exception.code)
        _logger.error('Unhandled Tan Phat API error', exc_info=(type(exception), exception, exception.__traceback__))
        return api_error('internal_error', 'An unexpected error occurred.', 500)
