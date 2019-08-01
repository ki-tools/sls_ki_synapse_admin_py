import pytest
import os
import json
import tempfile

# Load Environment variables.
module_dir = os.path.dirname(os.path.abspath(__file__))

test_env_file = os.path.join(module_dir, '../private.env.json')

if os.path.isfile(test_env_file):
    with open(test_env_file) as f:
        config = json.load(f).get('test')

        for key, value in config.items():
            os.environ[key] = value
else:
    print('WARNING: Test environment file not found at: {0}'.format(test_env_file))

# Import the remaining modules after the ENV variables have been loaded and set.
from tests.synapse_test_helper import SynapseTestHelper
from www.core import Synapse


@pytest.fixture(scope='session')
def syn_client():
    return Synapse.client()


@pytest.fixture()
def syn_test_helper():
    """
    Provides the SynapseTestHelper as a fixture per function.
    """
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


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
