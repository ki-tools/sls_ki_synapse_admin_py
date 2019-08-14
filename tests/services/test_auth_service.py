import pytest
import json
from www.core import ParamStore
from www.services import AuthService
import responses


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
def mk_stub_google_endpoints(request_base_url, google_provider_config_url, google_token_url, google_userinfo_url):
    def _mk(res_mock, with_provider_config=False, with_token=False, with_user_info=False, userinfo={}):
        if with_provider_config:
            # google_provider_config
            body = {
                'authorization_endpoint': google_provider_config_url,
                'token_endpoint': google_token_url,
                'userinfo_endpoint': google_userinfo_url
            }
            res_mock.add(responses.GET, ParamStore.GOOGLE_DISCOVERY_URL(), status=200, body=json.dumps(body))

        # google_token_endpoint
        if with_token:
            body = {
                'access_token': '999',
                "expires_in": 3599,
                "scope": "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
                "token_type": "Bearer",
                "id_token": "888"
            }
            res_mock.add(responses.POST, google_token_url, status=200, body=json.dumps(body))

        # google_userinfo_endpoint
        if with_user_info:
            body = {
                'email_verified': userinfo.get('is_verified', True),
                'sub': userinfo.get('user_id', 1),
                'email': userinfo.get('email', 'user@test.com'),
            }
            res_mock.add(responses.GET, google_userinfo_url, status=200, body=json.dumps(body))

    yield _mk


@pytest.fixture
def expected_redirect_uri(google_provider_config_url):
    return '{0}?response_type=code&client_id={1}&redirect_uri=https%3A%2F%2Fwww.test.com%2Fbase_url%2Fcallback&scope=openid+email+profile'.format(
        google_provider_config_url, ParamStore.GOOGLE_CLIENT_ID())


def test_get_redirect_uri(mk_stub_google_endpoints, request_base_url, expected_redirect_uri):
    with responses.RequestsMock() as res_mock:
        mk_stub_google_endpoints(res_mock, with_provider_config=True)
        redirect_uri = AuthService.get_redirect_uri(request_base_url)
        assert redirect_uri == expected_redirect_uri


def test_handle_callback_and_login(mk_stub_google_endpoints, request_base_url, mocker, monkeypatch):
    mock = mocker.patch.object(AuthService, 'login_user')
    mock.return_value = True

    email = 'random.user@test.com'
    monkeypatch.setenv('LOGIN_WHITELIST', email)
    assert email in ParamStore.LOGIN_WHITELIST()

    with responses.RequestsMock() as res_mock:
        mk_stub_google_endpoints(res_mock,
                                 with_provider_config=True,
                                 with_token=True,
                                 with_user_info=True,
                                 userinfo={'email': email})
        user = AuthService.handle_callback_and_login('123', request_base_url + '?code=123&state=abc', request_base_url)
        assert user is not None
        assert user.email == email


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
