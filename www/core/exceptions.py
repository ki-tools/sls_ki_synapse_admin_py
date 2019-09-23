class AuthEmailNotVerifiedError(ValueError):
    """Raised when a user's email is not validated with Google."""
    pass


class AuthForbiddenError(ValueError):
    """Raised when a user is forbidden from logging into the site."""
    pass


class AuthLoginFailureError(ValueError):
    """Raised when an unknown login failure occurs."""
    pass
