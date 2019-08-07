import pytest
from flask import url_for


def test_it_redirects_to_login(client):
    res = client.get('/synapse_space/create')
    assert res.status_code == 302
    assert res.location.endswith('/login?next=%2Fsynapse_space%2Fcreate')
