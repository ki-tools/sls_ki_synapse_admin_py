import pytest


@pytest.mark.usefixtures("login_enabled")
def test_it_loads_the_page(client):
    res = client.get('/login')
    assert res.status_code == 302
    assert res.location.endswith('/login')


@pytest.mark.usefixtures("login_enabled")
def test_it_passes_the_next_url(client):
    res = client.get('/login?next=/test/page')
    assert res.status_code == 302
    assert res.location.endswith('/login?next=%2Ftest%2Fpage')
