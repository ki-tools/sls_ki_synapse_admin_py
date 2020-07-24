from sls_tools.param_store import ParamStore
import uuid
import json


class Env:
    @staticmethod
    def FLASK_ENV(default='development'):
        """This variable must be set on the OS (not on SSM)"""
        return ParamStore.get('FLASK_ENV', default=default, store=ParamStore.Stores.OS).value

    @staticmethod
    def FLASK_DEBUG(default=False):
        """This variable must be set on the OS (not on SSM)"""
        return ParamStore.get('FLASK_DEBUG', default=default, store=ParamStore.Stores.OS).to_bool()

    @staticmethod
    def FLASK_TESTING(default=False):
        """This variable must be set on the OS (not on SSM)"""
        return ParamStore.get('FLASK_TESTING', default=default, store=ParamStore.Stores.OS).to_bool()

    @staticmethod
    def FLASK_LOGIN_DISABLED(default=False):
        """This variable must be set on the OS (not on SSM)"""
        return ParamStore.get('FLASK_LOGIN_DISABLED', default=default, store=ParamStore.Stores.OS).to_bool()

    @staticmethod
    def SERVICE_NAME(default=None):
        """This variable must be set on the OS (not on SSM)"""
        return ParamStore.get('SERVICE_NAME', default=default, store=ParamStore.Stores.OS).value

    @staticmethod
    def SERVICE_STAGE(default=None):
        """This variable must be set on the OS (not on SSM)"""
        return ParamStore.get('SERVICE_STAGE', default=default, store=ParamStore.Stores.OS).value

    @staticmethod
    def SECRET_KEY(default=str(uuid.uuid4())):
        return ParamStore.get('SECRET_KEY', default).value

    @staticmethod
    def LOG_LEVEL(default=None):
        return ParamStore.get('LOG_LEVEL', default).value

    @staticmethod
    def SYNAPSE_USERNAME(default=None):
        return ParamStore.get('SYNAPSE_USERNAME', default).value

    @staticmethod
    def SYNAPSE_PASSWORD(default=None):
        return ParamStore.get('SYNAPSE_PASSWORD', default).value

    @staticmethod
    def GOOGLE_CLIENT_ID(default=None):
        return ParamStore.get('GOOGLE_CLIENT_ID', default).value

    @staticmethod
    def GOOGLE_CLIENT_SECRET(default=None):
        return ParamStore.get('GOOGLE_CLIENT_SECRET', default).value

    @staticmethod
    def GOOGLE_DISCOVERY_URL(default='https://accounts.google.com/.well-known/openid-configuration'):
        return ParamStore.get('GOOGLE_DISCOVERY_URL', default).value

    @staticmethod
    def LOGIN_WHITELIST(default=[]):
        return ParamStore.get('LOGIN_WHITELIST', default).to_list(delimiter=',')

    @staticmethod
    def SYNAPSE_SPACE_LOG_FOLDER_ID(default=None):
        return ParamStore.get('SYNAPSE_SPACE_LOG_FOLDER_ID', default).value

    @staticmethod
    def SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID(default=None):
        return ParamStore.get('SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID', default).to_int()

    @staticmethod
    def SYNAPSE_SPACE_DCA_CREATE_CONFIG(default='[]'):
        return ParamStore.get('SYNAPSE_SPACE_DCA_CREATE_CONFIG', default).to_json()

    @staticmethod
    def SYNAPSE_SPACE_DCA_CREATE_CONFIG_by_id(id):
        configs = Env.SYNAPSE_SPACE_DCA_CREATE_CONFIG()
        return next((c for c in configs if c['id'] == id), None)

    @staticmethod
    def SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG(default='[]'):
        return ParamStore.get('SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG', default).to_json()

    @staticmethod
    def SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG_by_id(id):
        configs = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG()
        return next((c for c in configs if c['id'] == id), None)

    @staticmethod
    def get_daa_grant_access_data_collection_by_name(config, name):
        data_collections = config.get('data_collections', [])
        return next((c for c in data_collections if c['name'] == name), None)

    @staticmethod
    def get_default_daa_grant_access_config():
        # We only have one config now so hard code this until we have more.
        return Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_CONFIG()[0]

    class Test:
        @staticmethod
        def TEST_OTHER_SYNAPSE_USER_ID(default=None):
            return ParamStore.get('TEST_OTHER_SYNAPSE_USER_ID', default=default).to_int()

        @staticmethod
        def TEST_EMAIL(default=None):
            return ParamStore.get('TEST_EMAIL', default=default).value
