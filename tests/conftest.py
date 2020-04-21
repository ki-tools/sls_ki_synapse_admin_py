import pytest
import os
import json
import tempfile

# Load Environment variables.
import www.config as config

config.load_local(config.Envs.TEST)

# Import the remaining modules after the ENV variables have been loaded and set.
from www import server
from www.server import app
from tests.synapse_test_helper import SynapseTestHelper
from www.core import Synapse, Env

assert Env.FLASK_ENV() == config.Envs.TEST


@pytest.fixture
def test_app():
    with app.app_context():
        yield app


@pytest.fixture
def client(test_app):
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def login_enabled(test_app):
    test_app.config['LOGIN_DISABLED'] = False
    server.init_all()
    yield
    test_app.config['LOGIN_DISABLED'] = Env.FLASK_LOGIN_DISABLED()
    server.init_all()


@pytest.fixture(scope='session')
def syn_client():
    return Synapse.client()


@pytest.fixture
def syn_test_helper():
    """Provides the SynapseTestHelper as a fixture per function."""
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


@pytest.fixture
def fake_synapse_id(syn_test_helper):
    """Provides a Synapse entity ID that does not exist."""
    return syn_test_helper.fake_synapse_id()


@pytest.fixture
def temp_file(syn_test_helper):
    """Generates a temp file containing the SynapseTestHelper.uniq_name per function."""
    fd, tmp_filename = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(syn_test_helper.uniq_name())
    yield tmp_filename

    if os.path.isfile(tmp_filename):
        os.remove(tmp_filename)


@pytest.fixture
def mk_uniq_real_email(syn_test_helper):
    def _mk():
        test_email = Env.Test.TEST_EMAIL()
        name, domain = test_email.split('@')
        plus = '' if '+' in name else '+'
        return '{0}{1}{2}@{3}'.format(name, plus, syn_test_helper.uniq_name(), domain)

    yield _mk


def open_json_config(filename):
    with open(os.path.join(app.root_path, '..', 'templates', filename), mode='r') as f:
        config = json.load(f)

    # Clear all the data.
    id_index = 1
    for obj in config:
        for key, value in obj.items():
            if isinstance(obj[key], str):
                obj[key] = ''
            elif isinstance(obj[key], list):
                obj[key] = []
        obj['id'] = str(id_index)
        id_index += 1

    return config


@pytest.fixture
def dca_config():
    config = open_json_config('private.dca.create.space.json')
    return config[0]


@pytest.fixture
def daa_config(syn_test_helper, monkeypatch):
    config = open_json_config('private.daa.grant.access.json')
    return config[0]
