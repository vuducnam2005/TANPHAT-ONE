import logging


class ApiProblem(Exception):
    """API error with a stable code and optional structured details.

    Raising it rolls the request transaction back like any other exception;
    ``ir.http`` turns it into the standard error envelope. These are expected
    client outcomes, so the Odoo router logs them at ``loglevel`` instead of as
    unhandled request exceptions.
    """

    loglevel = logging.INFO

    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details
