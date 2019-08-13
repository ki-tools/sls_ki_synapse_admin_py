from www import server
from www.core import ParamStore, AuthEmailNotVerifiedError, AuthForbiddenError, AuthLoginFailureError
from www.models import User
import json
import requests
from flask_login import login_user, logout_user


class AuthService:

    @classmethod
    def get_redirect_uri(cls, request_base_url):
        """
        Gets the Google auth sign in URI.
        This is the URI that the app will redirect the user to so they can sign into Google.

        :param request_base_url: The login request.base_url
        :return: URL
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
        """
        Handles the Google oauth callback and logs the user in, or raises an exception.

        :param code: Authorization code Google sent back.
        :param request_url: The callback request.url
        :param request_base_url: The callback request.base_url
        :return: The logged in user.
        :raises AuthEmailNotVerifiedError, AuthForbiddenError
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
            auth=(ParamStore.GOOGLE_CLIENT_ID(), ParamStore.GOOGLE_CLIENT_SECRET()),
        )

        # Parse the tokens
        server.auth_client.parse_request_body_response(json.dumps(token_response.json()))

        # Now that you have tokens let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email.
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = server.auth_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        res_json = userinfo_response.json()

        email_verified = res_json.get("email_verified", False)
        unique_id = res_json.get("sub", None)
        users_email = res_json.get("email", None)

        if not email_verified:
            raise AuthEmailNotVerifiedError()

        if not cls.user_allowed_login(users_email):
            raise AuthForbiddenError('Email: {0} not allowed to login.'.format(users_email))

        user = User(unique_id, users_email)
        if cls.login_user(user):
            return user
        else:
            raise AuthLoginFailureError()

    @classmethod
    def user_allowed_login(cls, email):
        """
        Gets if an email address is allowed to login into the site.

        :param email: The email address to check against the whitelist of emails.
        :return: True or False
        """
        whitelist = ParamStore.LOGIN_WHITELIST() or ''
        allowed_emails = [e.strip() for e in whitelist.split(',') if e and e.strip()]
        return email in allowed_emails

    @classmethod
    def login_user(cls, user):
        return login_user(user)

    @classmethod
    def logout_user(cls):
        """
        Logs out the current user.

        :return: True
        """
        return logout_user()

    @classmethod
    def get_google_provider_config(cls):
        """
        Gets the Google auth provider configuration.

        :return:
        """
        return requests.get(ParamStore.GOOGLE_DISCOVERY_URL()).json()
