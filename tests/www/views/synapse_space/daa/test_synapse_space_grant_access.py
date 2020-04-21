import pytest
import json


@pytest.fixture
def url_path():
    return '/synapse_space/daa/grant'


@pytest.fixture(autouse=True)
def provide_dca_config(daa_config, monkeypatch):
    monkeypatch.setenv('SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG', json.dumps([daa_config]))


@pytest.mark.usefixtures("login_enabled")
def test_it_redirects_to_login(client, url_path):
    res = client.get(url_path)
    assert res.status_code == 302
    assert res.location.endswith('/login?next=%2Fsynapse_space%2Fdaa%2Fgrant')


def test_it_loads_the_page(client, url_path):
    res = client.get(url_path)
    assert res.status_code == 200
