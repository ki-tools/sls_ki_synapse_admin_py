import pytest
import os
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
    """
    Provides the SynapseTestHelper as a fixture per function.
    """
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


@pytest.fixture
def fake_synapse_id(syn_test_helper):
    """
    Provides a Synapse entity ID that does not exist.
    """
    return syn_test_helper.fake_synapse_id()


@pytest.fixture
def temp_file(syn_test_helper):
    """
    Generates a temp file containing the SynapseTestHelper.uniq_name per function.
    """
    fd, tmp_filename = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(syn_test_helper.uniq_name())
    yield tmp_filename

    if os.path.isfile(tmp_filename):
        os.remove(tmp_filename)
