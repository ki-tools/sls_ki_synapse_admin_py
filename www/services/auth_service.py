from www import server
from www.core import Env, AuthEmailNotVerifiedError, AuthForbiddenError, AuthLoginFailureError
from www.models import User
from www.core.log import logger
import json
import requests
from flask_login import login_user, logout_user


class AuthService:

    @classmethod
    def get_redirect_uri(cls, request_base_url):
        """Gets the Google auth sign in URI.

        This is the URI that the app will redirect the user to so they can sign into Google.

        Args:
            request_base_url: The login request.base_url

        Returns:
            URL
        """
        # Find out what URL to hit for Google login
        google_provider_cfg = cls.get_google_provider_config()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        request_uri = server.auth_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request_base_url + "/callback",
            scope=["openid", "email", "profile"],
        )
        return request_uri

    @classmethod
    def handle_callback_and_login(cls, code, request_url, request_base_url):
        """Handles the Google oauth callback and logs the user in, or raises an exception.

        Args:
            code: Authorization code Google sent back.
            request_url: The callback request.url
            request_base_url: The callback request.base_url

        Returns:
            The logged in user.

        Raises:
           AuthEmailNotVerifiedError, AuthForbiddenError
        """
        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user.
        google_provider_cfg = cls.get_google_provider_config()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens.
        token_url, headers, body = server.auth_client.prepare_token_request(
            token_endpoint,
            authorization_response=request_url,
            redirect_url=request_base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(Env.GOOGLE_CLIENT_ID(), Env.GOOGLE_CLIENT_SECRET()),
        )

        # Parse the tokens
        server.auth_client.parse_request_body_response(json.dumps(token_response.json()))

        # Now that we have tokens let's find and hit the URL
        # from Google that gives the user's profile information,
        # including their Google profile image and email.
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = server.auth_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        res_json = userinfo_response.json()

        email_verified = res_json.get("email_verified", False)
        unique_id = res_json.get("sub", None)
        users_email = res_json.get("email", None)

        if not email_verified:
            err_str = 'Email not verified by Google: {0}'.format(users_email)
            logger.info(err_str)
            raise AuthEmailNotVerifiedError(err_str)

        if not cls.user_allowed_login(users_email):
            err_str = 'Email not allowed to login: {0}'.format(users_email)
            logger.info(err_str)
            raise AuthForbiddenError(err_str)

        user = User(unique_id, users_email)
        if cls.login_user(user):
            return user
        else:
            raise AuthLoginFailureError('Unknown error logging user in.')

    @classmethod
    def user_allowed_login(cls, email):
        """Gets if an email address is allowed to login to the site.

        Args:
            email: The email address to check against the whitelist of emails.

        Returns:
            True or False
        """
        return email in Env.LOGIN_WHITELIST(default=[])

    @classmethod
    def login_user(cls, user):
        """Logs a user in.

        Args:
            user: The user to login.

        Returns:
            True
        """
        logger.info('Logging user in: {0} ({1})'.format(user.email, user.id))
        return login_user(user)

    @classmethod
    def logout_user(cls):
        """Logs the current user out.

        Returns:
            True
        """
        return logout_user()

    @classmethod
    def get_google_provider_config(cls):
        """Gets the Google auth provider configuration.

        Returns:
            Google config has a hash.
        """
        return requests.get(Env.GOOGLE_DISCOVERY_URL()).json()
