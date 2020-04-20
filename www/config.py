import os
import json
from www.core import Env


class Envs:
    PRODUCTION = 'production'
    STAGING = 'staging'
    DEVELOPMENT = 'development'
    TEST = 'test'
    ALL = [PRODUCTION, STAGING, DEVELOPMENT, TEST]
    ALLOWED_LOCAL_ENVS = [DEVELOPMENT, TEST]


def load_local_if_applicable():
    """Load the local environment variables if an applicable environment is set.

    Returns:
        True if the correct environment is set and the config file was found and loaded else False.
    """
    if Env.FLASK_ENV() in Envs.ALLOWED_LOCAL_ENVS:
        return load_local(Env.FLASK_ENV())


def load_local(flask_env):
    """Loads environment variables from a local config file.

    This should only be called when locally developing or running tests.
    In production or CI all variables must be set in the OS environment or SSM.

    Args:
        flask_env: Which environment to load from the config file.

    Returns:
        True if the file was found and loaded else False.
    """
    if flask_env not in Envs.ALLOWED_LOCAL_ENVS:
        raise ValueError('FLASK_ENV not allowed: {0}'.format(flask_env))

    env_vars = open_local(flask_env, 'private.dev.env.json')

    for key, value in env_vars.items():
        if value is None:
            print('WARNING: Environment variable: {0} has no value and will not be set.'.format(key))
        else:
            os.environ[key] = value

    return False


def open_local(flask_env, filename):
    """Opens a local config file and parses it.

    Args:
        flask_env: Which environment to load from the config file.
        filename: The full path to the config file to open.

    Returns:
        Dict of environment variables.
    """
    module_dir = os.path.dirname(os.path.abspath(__file__))
    src_root_dir = os.path.abspath(os.path.join(module_dir, '..'))
    env_file = os.path.join(src_root_dir, filename)

    result = {}

    if os.path.isfile(env_file):
        print('Loading local configuration from: {0}'.format(env_file))

        config = json.loads(_read_file(env_file)).get(flask_env)

        for key, value in config.items():
            if value is None:
                print('WARNING: Environment variable: {0} has no value and will not be set.'.format(key))
            else:
                parsed_value = value

                if str(value).startswith('$ref:'):
                    filename = value.replace('$ref:', '')
                    parsed_value = _read_file(filename)

                result[key] = parsed_value
    else:
        print('WARNING: Configuration file not found at: {0}'.format(env_file))

    return result


def _read_file(path):
    with open(path, mode='r') as f:
        return f.read()
