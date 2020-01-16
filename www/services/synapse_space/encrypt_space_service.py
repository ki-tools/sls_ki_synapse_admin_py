from www.core import Synapse, Env
from www.core.log import logger
import synapseclient as syn
from synapseclient.exceptions import SynapseHTTPError


class EncryptSpaceService:
    def __init__(self, project_id):
        """Instantiates a new instance.

        Args:
            project_id: The Project ID to set the storage location on.
        """
        self.project_id = project_id
        self.errors = []

    def execute(self):
        """Sets the storage location of the Project.

        This method does not do validation. It expects all validation to have been done and passed already.

        Returns:
            Self
        """
        self.errors = []

        try:
            storage_location_id = Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()
            if storage_location_id:
                logger.info(
                    'Setting storage location on project: {0} to: {1}'.format(self.project_id, storage_location_id))
                Synapse.client().setStorageLocation(self.project_id, storage_location_id)
                logger.info('Storage location set on project: {0}'.format(self.project_id))
            else:
                self.errors.append(
                    'Environment Variable: SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID not set. Storage location cannot be set.')
        except Exception as ex:
            logger.exception(ex)
            self.errors.append('Error setting storage location: {0}'.format(ex))

        return self

    class Validations:

        @classmethod
        def validate(cls, project_id):
            """Validates that the Project can have its storage setting changed.

            Args:
                project_id: Project (or None) and error message (or None)

            Returns:
                Project (or None) and error message (or None)
            """
            project, error = cls._get_project(project_id)
            if not error:
                storage_setting, error = cls._get_project_storage_setting(project_id)

            return project, error

        @classmethod
        def _get_project(cls, project_id):
            """Gets the Project from Synapse.

            Args:
                project_id:

            Returns:
                Project (or None) and error message (or None)
            """
            project = None
            error = None
            try:
                project = Synapse.client().get(syn.Project(id=project_id))
            except SynapseHTTPError as ex:
                logger.exception(ex)
                if ex.response.status_code == 404:
                    error = 'Synapse project ID: {0} does not exist.'.format(project_id)
                elif ex.response.status_code == 403:
                    error = 'This service (Synapse user: {0}) does not have access to Synapse project ID: {1}'.format(
                        Env.SYNAPSE_USERNAME(), project_id)
                else:
                    error = 'Error getting synapse project: {0}'.format(ex)

            return project, error

        @classmethod
        def _get_project_storage_setting(cls, project_id):
            """Gets the storage setting for the Project.

            Args:
                project_id: The Project to get storage settings for.

            Returns:
                Storage setting (or None) and error message (or None)
            """
            storage_setting = None
            error = None

            # Check if the project is already encrypted.
            try:
                storage_id = Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()
                storage_setting = Synapse.client().getProjectSetting(project_id, 'upload')

                if storage_setting is not None:
                    storage_ids = storage_setting.get('locations')
                    if storage_id in storage_ids:
                        error = 'Storage location already set for Synapse project: {0}'.format(project_id)
            except SynapseHTTPError as ex:
                logger.exception(ex)
                if ex.response.status_code == 403:
                    error = 'This service (Synapse user: {0}) does not have administrator access to Synapse project: {0}'.format(
                        Env.SYNAPSE_USERNAME(), project_id)
                else:
                    error = 'Error getting storage settings: {0}'.format(ex)

            return storage_setting, error
