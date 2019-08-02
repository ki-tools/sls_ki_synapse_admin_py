import os
import boto3
import logging
import uuid


class ParamStore:

    @classmethod
    def get(cls, key, default=None, only_from_env=False):
        """
        Tries to get a value from the OS then SSM otherwise it returns the default value.
        """
        # Try to get the value from the local environment.
        result = cls._get_from_os(key)
        if result is not None:
            return result

        # Try to get the value from SSM.
        if not only_from_env:
            result = cls._get_from_ssm(key)
            if result is not None:
                return result

        return default

    @classmethod
    def get_bool(cls, key, default=False, only_from_env=False):
        """
        Tries to get a boolean value from the OS then SSM otherwise it returns the default value.
        """
        value = cls.get(key, default=default, only_from_env=only_from_env)

        if isinstance(value, bool):
            return value
        elif value is None:
            return False
        else:
            return str(value).lower() == 'true'

    @classmethod
    def get_int(cls, key, default=None, only_from_env=False):
        """
        Tries to get an integer value from the OS then SSM otherwise it returns the default value.
        """
        value = cls.get(key, default=default, only_from_env=only_from_env)

        if isinstance(value, int):
            return value
        elif value is not None and str(value).strip() == '':
            value = None
        elif value is not None:
            return int(value)

    @classmethod
    def _get_from_os(cls, key):
        """
        Gets a value from the OS.
        """
        return os.environ.get(key)

    @classmethod
    def _get_from_ssm(cls, key):
        """
        Gets a value from SSM.
        """
        ssm_key = cls._build_ssm_key(key)
        result = None

        try:
            client = boto3.client('ssm')
            try:
                get_response = client.get_parameter(Name=ssm_key, WithDecryption=True)
                result = get_response.get('Parameter').get('Value')
            except client.exceptions.ParameterNotFound:
                logging.exception('SSM Parameter Not Found: {}'.format(ssm_key))
        except Exception as ex:
            logging.exception('SSM Error: {}'.format(str(ex)))

        return result

    @classmethod
    def _set_ssm_parameter(cls, key, value, type='SecureString'):
        """
        Sets an SSM key/value.
        """
        ssm_key = cls._build_ssm_key(key)

        try:
            client = boto3.client('ssm')
            try:
                return client.put_parameter(Name=ssm_key, Value=value, Type=type, Overwrite=True)
            except client.exceptions.ParameterNotFound:
                logging.exception('SSM Parameter Not Found: {}'.format(ssm_key))
        except Exception as ex:
            logging.exception('SSM Error: {}'.format(str(ex)))

    @classmethod
    def _delete_ssm_parameter(cls, key):
        """
        Deletes an SSM key.
        """
        ssm_key = cls._build_ssm_key(key)

        try:
            client = boto3.client('ssm')
            try:
                client.delete_parameter(Name=ssm_key)
                return True
            except client.exceptions.ParameterNotFound:
                logging.exception('SSM Parameter Not Found: {}'.format(ssm_key))
        except Exception as ex:
            logging.exception('SSM Error: {}'.format(str(ex)))

        return False

    @classmethod
    def _build_ssm_key(cls, key):
        """
        Builds a SSM key in the format for service_name/service_stage/key.
        """
        service_name = cls._get_from_os('SERVICE_NAME')
        service_stage = cls._get_from_os('SERVICE_STAGE')

        if not service_name:
            raise KeyError('Environment variable not set: SERVICE_NAME')

        if not service_stage:
            raise KeyError('Environment variable not set: SERVICE_STAGE')

        return '/{0}/{1}/{2}'.format(service_name, service_stage, key)

    """
    ===============================================================================================
    Getter Methods.
    ===============================================================================================
    """

    @classmethod
    def FLASK_ENV(cls, default='development'):
        """
        This variable must be set on the OS (not on SSM)
        """
        return cls.get('FLASK_ENV', default=default, only_from_env=True)

    @classmethod
    def FLASK_DEBUG(cls, default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return cls.get_bool('FLASK_DEBUG', default=default, only_from_env=True)

    @classmethod
    def FLASK_TESTING(cls, default=False):
        """
        This variable must be set on the OS (not on SSM)
        """
        return cls.get_bool('FLASK_TESTING', default=default, only_from_env=True)

    @classmethod
    def SERVICE_NAME(cls, default=None):
        """
        This variable must be set on the OS (not on SSM)
        """
        return cls.get('SERVICE_NAME', default=default, only_from_env=True)

    @classmethod
    def SERVICE_STAGE(cls, default=None):
        """
        This variable must be set on the OS (not on SSM)
        """
        return cls.get('SERVICE_STAGE', default=default, only_from_env=True)

    @classmethod
    def SECRET_KEY(cls, default=str(uuid.uuid4())):
        return cls.get('SECRET_KEY', default)

    @classmethod
    def LOG_LEVEL(cls, default=None):
        return cls.get('LOG_LEVEL', default)

    @classmethod
    def SYNAPSE_USERNAME(cls, default=None):
        return cls.get('SYNAPSE_USERNAME', default)

    @classmethod
    def SYNAPSE_PASSWORD(cls, default=None):
        return cls.get('SYNAPSE_PASSWORD', default)

    @classmethod
    def SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID(cls, default=None):
        return cls.get_int('SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID', default)

    @classmethod
    def GOOGLE_CLIENT_ID(cls, default=None):
        return cls.get('GOOGLE_CLIENT_ID', default)

    @classmethod
    def GOOGLE_CLIENT_SECRET(cls, default=None):
        return cls.get('GOOGLE_CLIENT_SECRET', default)

    @classmethod
    def GOOGLE_DISCOVERY_URL(cls, default='https://accounts.google.com/.well-known/openid-configuration'):
        return cls.get('GOOGLE_DISCOVERY_URL', default)

    @classmethod
    def LOGIN_WHITELIST(cls, default=None):
        return cls.get('LOGIN_WHITELIST', default)
