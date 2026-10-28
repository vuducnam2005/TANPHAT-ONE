class ContractWorkflowError(Exception):
    """Business outcome of a contract workflow action, mapped to an API error by callers.

    ``status`` follows the API contract: 400 malformed payload, 403 missing
    capability, 404 outside the caller's scope, 409 state/version/idempotency
    conflict and 422 business validation. Raising it rolls the action back.
    """

    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details
