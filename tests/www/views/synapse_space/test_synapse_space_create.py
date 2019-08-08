import pytest


@pytest.fixture
def url_path():
    return '/synapse_space/create'


@pytest.mark.usefixtures("login_enabled")
def test_it_redirects_to_login(client, url_path):
    res = client.get(url_path)
    assert res.status_code == 302
    assert res.location.endswith('/login?next=%2Fsynapse_space%2Fcreate')


def test_it_loads_the_page(client, url_path):
    res = client.get(url_path)
    assert res.status_code == 200
