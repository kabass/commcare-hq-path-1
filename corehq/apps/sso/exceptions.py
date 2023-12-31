class ServiceProviderCertificateError(Exception):
    pass


class SingleSignOnError(Exception):
    pass


class SsoLoginFailed(Exception):
    pass


class OidcSsoError(Exception):
    USER_PERMISSION_ISSUE = "oidc_user_permission_issue"
    SESSION_UNKNOWN = "oidc_session_unknown"
    METHOD_NOT_ALLOWED = "oidc_method_not_allowed"
    OP_ERROR_MESSAGE = 'oidc_op_error_message'

    def __init__(self, error_code, message=None):
        super().__init__()
        self.code = error_code
        self.message = message
