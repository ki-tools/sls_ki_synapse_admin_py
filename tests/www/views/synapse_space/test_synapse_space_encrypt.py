import pytest
from flask_login import encode_cookie


def test_it_redirects_to_login(client):
    res = client.get('/synapse_space/encrypt')
    assert res.status_code == 302
    assert res.location.endswith('/login?next=%2Fsynapse_space%2Fencrypt')


@pytest.mark.usefixtures("authenticated_request")
def test_it_loads_the_page(client):
    res = client.get('/synapse_space/encrypt')
    assert res.status_code == 200
