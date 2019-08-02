import re
from www.core import Synapse, ParamStore
import synapseclient as syn


class EncryptSynapseSpaceService(object):
    def __init__(self, project_id):
        self.project_id = project_id

    def execute(self):
        errors = []

        try:
            storage_location_id = ParamStore.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()
            Synapse.client().setStorageLocation(self.project_id, storage_location_id)
        except Exception as ex:
            # TODO: log this.
            errors.append('Unknown error setting storage location.')

        return errors
