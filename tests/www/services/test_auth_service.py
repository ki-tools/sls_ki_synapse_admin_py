import pytest
import json
from www.core import WWWEnv, AuthEmailNotVerifiedError, AuthForbiddenError, AuthLoginFailureError
from www.services import AuthService
import responses


@pytest.fixture
def call_handle_callback_and_login(request_base_url):
    def _call():
        return AuthService.handle_callback_and_login('123', request_base_url + '?code=123&state=abc', request_base_url)

    yield _call


@pytest.fixture
def request_base_url():
    return 'https://www.test.com/base_url'


@pytest.fixture
def google_provider_config_url():
    return 'https://www.test.com/google_provider_config'


@pytest.fixture
def google_token_url():
    return 'https://www.test.com/token'


@pytest.fixture
def google_userinfo_url():
    return 'https://www.test.com/google_userinfo'


@pytest.fixture
def mk_stub_google_endpoints(request_base_url, google_provider_config_url, google_token_url, google_userinfo_url,
                             mocker, monkeypatch):
    def _mk(res_mock,
            with_all=False,
            with_provider_config=False,
            with_token=False,
            with_user_info=False,
            userinfo={},
            login_whitelist='',
            login_user_return_value=True):

        if with_provider_config or with_all:
            # google_provider_config
            body = {
                'authorization_endpoint': google_provider_config_url,
                'token_endpoint': google_token_url,
                'userinfo_endpoint': google_userinfo_url
            }
            res_mock.add(responses.GET, WWWEnv.GOOGLE_DISCOVERY_URL(), status=200, body=json.dumps(body))

        # google_token_endpoint
        if with_token or with_all:
            body = {
                'access_token': '999',
                "expires_in": 3599,
                "scope": "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
                "token_type": "Bearer",
                "id_token": "888"
            }
            res_mock.add(responses.POST, google_token_url, status=200, body=json.dumps(body))

        # google_userinfo_endpoint
        user_info_body = None
        if with_user_info or with_all:
            user_info_body = {
                'email_verified': userinfo.get('email_verified', True),
                'sub': userinfo.get('user_id', 1),
                'email': userinfo.get('email', 'user@test.com'),
            }
            res_mock.add(responses.GET, google_userinfo_url, status=200, body=json.dumps(user_info_body))

        if isinstance(login_whitelist, bool) and login_whitelist is True and user_info_body is not None:
            login_whitelist = user_info_body.get('email')

        if login_whitelist:
            monkeypatch.setenv('LOGIN_WHITELIST', login_whitelist)

        mock = mocker.patch.object(AuthService, 'login_user')
        mock.return_value = login_user_return_value

    yield _mk


@pytest.fixture
def expected_redirect_uri(google_provider_config_url):
    return '{0}?response_type=code&client_id={1}&redirect_uri=https%3A%2F%2Fwww.test.com%2Fbase_url%2Fcallback&scope=openid+email+profile'.format(
        google_provider_config_url, WWWEnv.GOOGLE_CLIENT_ID())


def test_get_redirect_uri(mk_stub_google_endpoints, request_base_url, expected_redirect_uri):
    with responses.RequestsMock() as res_mock:
        mk_stub_google_endpoints(res_mock, with_provider_config=True)
        redirect_uri = AuthService.get_redirect_uri(request_base_url)
        assert redirect_uri == expected_redirect_uri


def test_handle_callback_and_login(mk_stub_google_endpoints, call_handle_callback_and_login, monkeypatch):
    with responses.RequestsMock() as res_mock:
        email = 'random.user@test.com'
        mk_stub_google_endpoints(res_mock, with_all=True, userinfo={'email': email}, login_whitelist=True)
        assert email in WWWEnv.LOGIN_WHITELIST()
        user = call_handle_callback_and_login()
        assert user is not None
        assert user.email == email


def test_callback_raises_email_not_verified_error(mk_stub_google_endpoints, call_handle_callback_and_login):
    with responses.RequestsMock() as res_mock:
        mk_stub_google_endpoints(res_mock, with_all=True, userinfo={'email_verified': False})

        with pytest.raises(AuthEmailNotVerifiedError):
            call_handle_callback_and_login()


def test_callback_raises_forbidden_error(mk_stub_google_endpoints, call_handle_callback_and_login):
    with responses.RequestsMock() as res_mock:
        email = 'user.not.in.whitelist@test.com'
        mk_stub_google_endpoints(res_mock, with_all=True, userinfo={'email': email}, login_whitelist=False)

        with pytest.raises(AuthForbiddenError):
            call_handle_callback_and_login()


def test_callback_raises_login_failure_error(mk_stub_google_endpoints, call_handle_callback_and_login):
    with responses.RequestsMock() as res_mock:
        mk_stub_google_endpoints(res_mock,
                                 with_all=True,
                                 login_whitelist=True,
                                 login_user_return_value=False)

        with pytest.raises(AuthLoginFailureError):
            call_handle_callback_and_login()


def test_user_allowed_login(monkeypatch):
    emails = ['user1@test.com', 'user2@test.com', 'user3@test.com']

    # Test single emails in the whitelist.
    for email in emails:
        monkeypatch.delenv('LOGIN_WHITELIST', raising=False)

        assert AuthService.user_allowed_login(email) is False
        monkeypatch.setenv('LOGIN_WHITELIST', email)
        assert AuthService.user_allowed_login(email) is True
        assert AuthService.user_allowed_login('x{0}'.format(email)) is False

    # Test all emails in the whitelist.
    monkeypatch.setenv('LOGIN_WHITELIST', '  ,  '.join(emails))
    for email in emails:
        assert AuthService.user_allowed_login(email) is True
        assert AuthService.user_allowed_login('x{0}'.format(email)) is False

    # Test poorly formatted email list.
    monkeypatch.setenv('LOGIN_WHITELIST', 'user1@test.com,,  , ')
    assert AuthService.user_allowed_login('user1@test.com') is True
    assert AuthService.user_allowed_login('user1') is False
    assert AuthService.user_allowed_login('user1@') is False
    assert AuthService.user_allowed_login('user1@test') is False
    assert AuthService.user_allowed_login('test.com') is False
    assert AuthService.user_allowed_login('@test.com') is False
    assert AuthService.user_allowed_login('') is False
    assert AuthService.user_allowed_login(None) is False


def test_login_user():
    # TODO: test this
    pass


def test_logout_user():
    # TODO: test this
    pass
