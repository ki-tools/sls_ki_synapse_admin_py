import pytest
from www.services import AuthService


@pytest.fixture
def request_base_url():
    return 'https://www.test.com/app'


@pytest.fixture
def expected_redirect_uri():
    return 'https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=set-this&redirect_uri=https%3A%2F%2Fwww.test.com%2Fapp%2Fcallback&scope=openid+email+profile'


@pytest.fixture
def stub_get_google_provider_cfg():
    pass


def test_it_gets_the_redirect_uri(request_base_url, expected_redirect_uri, stub_get_google_provider_cfg):
    res = AuthService.get_redirect_uri(request_base_url)

    # TODO: Stub this method on the AuthService?
    # get_google_provider_cfg

    assert res == expected_redirect_uri
