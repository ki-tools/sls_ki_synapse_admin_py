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
def blank_dca_config():
    config = open_json_config('private.dca.create.space.json')
    return config[0]


@pytest.fixture
def blank_basic_config():
    config = open_json_config('private.basic.create.space.json')
    return config[0]


@pytest.fixture
def blank_daa_config(syn_test_helper, monkeypatch):
    config = open_json_config('private.daa.grant.access.json')
    return config[0]


@pytest.fixture
def set_dca_config(monkeypatch):
    orig_config = Env.SYNAPSE_SPACE_DCA_CREATE_CONFIG()

    def _set(config):
        # Set the config in the Env so it's available.
        monkeypatch.setenv('SYNAPSE_SPACE_DCA_CREATE_CONFIG', json.dumps(config))

    yield _set
    # Revert back to the original config.
    monkeypatch.setenv('SYNAPSE_SPACE_DCA_CREATE_CONFIG', orig_config)


@pytest.fixture
def set_basic_config(monkeypatch):
    orig_config = Env.SYNAPSE_SPACE_BASIC_CREATE_CONFIG()

    def _set(config):
        # Set the config in the Env so it's available.
        monkeypatch.setenv('SYNAPSE_SPACE_BASIC_CREATE_CONFIG', json.dumps(config))

    yield _set
    # Revert back to the original config.
    monkeypatch.setenv('SYNAPSE_SPACE_BASIC_CREATE_CONFIG', orig_config)


@pytest.fixture
def set_daa_config(monkeypatch):
    orig_config = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG()

    def _set(config):
        # Set the config in the Env so it's available.
        monkeypatch.setenv('SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG', json.dumps(config))

    yield _set
    # Revert back to the original config.
    monkeypatch.setenv('SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG', orig_config)


@pytest.fixture
def dca_config(blank_dca_config, set_dca_config):
    config = blank_dca_config.copy()
    config['id'] = '1'
    config['name'] = 'Config 01'
    # config['wiki_project_id'] = None
    # config['contribution_agreement_table_id'] = None
    # config['contributor_tracking_view_id'] = None
    # config['team_manager_user_ids'] = []
    config['folder_names'] = ['Folder 1', 'Folder 2']
    # config['project_access'] = []
    # config['team_entity_access'] = []
    config['additional_parties'] = [
        {
            "code": "CODE_1",
            "name": "Code 1"
        },
        {
            "code": "CODE_2",
            "name": "Code 2"
        }
    ]
    set_dca_config([config])

    return config


@pytest.fixture
def basic_config(blank_basic_config, set_basic_config):
    config = blank_basic_config.copy()
    config['id'] = '1'
    config['name'] = 'Config 01'
    # config['contributor_tracking_view_id'] = None
    set_basic_config([config])

    return config


@pytest.fixture
def daa_config(blank_daa_config, set_daa_config):
    config = blank_daa_config.copy()
    config['id'] = '1'
    config['name'] = 'Config 01'
    # config['agreement_table_id'] = None
    config['team_manager_user_ids'] = []
    config['data_collections'] = [
        {
            'name': 'Collection 1',
            'include_collection_name_in_team_name': True,
            'entities': []
        }
    ]
    config['additional_parties'] = [
        {
            "code": "CODE_1",
            "name": "Code 1"
        },
        {
            "code": "CODE_2",
            "name": "Code 2"
        }
    ]
    set_daa_config([config])

    return config
