import os
import json
from www.core import ParamStore


class Envs:
    PRODUCTION = 'production'
    STAGING = 'staging'
    DEVELOPMENT = 'development'
    TEST = 'test'
    ALL = [PRODUCTION, STAGING, DEVELOPMENT, TEST]
    ALLOWED_LOCAL_ENVS = [DEVELOPMENT, TEST]


def load_local_if_applicable():
    """
    Load the local environment variables if an applicable environment is set.

    :return: True if the correct environment is set and the config file was found and loaded else False.
    """
    if ParamStore.FLASK_ENV() in Envs.ALLOWED_LOCAL_ENVS:
        return load_local(ParamStore.FLASK_ENV())


def load_local(flask_env):
    """
    Loads environment variables from a local config file.
    This should only be called when locally developing or running tests.
    In production or CI all variables must be set in the environment.

    :param flask_env: Which environment to load from the config file.
    :return: True if the file was found and loaded else False.
    """
    if flask_env not in Envs.ALLOWED_LOCAL_ENVS:
        raise ValueError('FLASK_ENV not allowed: {0}'.format(flask_env))

    module_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(module_dir, '../private.dev.env.json')

    if os.path.isfile(env_file):
        print('Loading local configuration from: {0}'.format(env_file))

        with open(env_file) as f:
            config = json.load(f).get(flask_env)

            for key, value in config.items():
                os.environ[key] = value
        return True
    else:
        print('WARNING: Configuration file not found at: {0}'.format(env_file))

    return False
