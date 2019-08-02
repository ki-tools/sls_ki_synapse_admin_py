from www.core import Synapse, ParamStore
import synapseclient as syn
from synapseclient.exceptions import SynapseHTTPError


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

    def validate(self):
        project = None
        error = None

        project, error = self._get_project()
        if not error:
            storage_setting, error = self._get_storage_info(project)

        return project, error

    def _get_project(self):
        project = None
        error = None
        try:
            project = Synapse.client().get(syn.Project(id=self.project_id))
        except SynapseHTTPError as ex:
            if ex.response.status_code == 404:
                error = 'Synapse project ID: {0} does not exist.'.format(self.project_id)
            elif ex.response.status_code == 403:
                error = 'This service (Synapse user: {0}) does not have access to Synapse project ID: {1}'.format(
                    ParamStore.SYNAPSE_USERNAME(), self.project_id)
            else:
                error = 'Unknown error getting synapse project.'

        return project, error

    def _get_storage_info(self, project):
        storage_setting = None
        error = None

        # Check if the project is already encrypted.
        try:
            storage_id = ParamStore.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()
            storage_setting = Synapse.client().getProjectSetting(project, 'upload')

            if storage_setting is not None:
                storage_ids = storage_setting.get('locations')
                if storage_id in storage_ids:
                    error = 'Storage location already set for Synapse project: {0} ({1})'.format(project.name,
                                                                                                 project.id)
        except SynapseHTTPError as ex:
            if ex.response.status_code == 403:
                error = 'This service (Synapse user: {0}) does not have administrator access to Synapse project: {0} ({1})'.format(
                    ParamStore.SYNAPSE_USERNAME(), project.name, project.id)
            else:
                error = 'Unknown error getting storage settings.'

        return storage_setting, error
