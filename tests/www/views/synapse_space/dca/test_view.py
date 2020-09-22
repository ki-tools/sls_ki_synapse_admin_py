import pytest
import json


@pytest.fixture
def url_path():
    return '/synapse_space/dca/create'


@pytest.fixture(autouse=True)
def provide_dca_config(dca_config):
    # This is just to get the config loaded into the ENV.
    pass


@pytest.mark.usefixtures("login_enabled")
def test_it_redirects_to_login(client, url_path):
    res = client.get(url_path)
    assert res.status_code == 302
    assert res.location.endswith('/synapse_space/dca/create')


def test_it_loads_the_page(client, url_path):
    res = client.get(url_path, follow_redirects=True)
    assert res.status_code == 200
