class AuthEmailNotVerified(ValueError):
    """
    Raised when a user's email is not validated with Google.
    """
    pass


class AuthForbidden(ValueError):
    """
    Raised when a user is forbidden from logging into the site.
    """
    pass
