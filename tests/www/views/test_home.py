import pytest


@pytest.mark.usefixtures("login_enabled")
def test_it_loads_the_page(client):
    res = client.get('/')
    assert res.status_code == 200
