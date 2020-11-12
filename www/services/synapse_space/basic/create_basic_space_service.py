import os
import json
import shutil
import tempfile
from datetime import datetime
from www.core import Env
from www.core.log import logger
from www.core.synapse import Synapse
import synapseclient as syn


class CreateBasicSpaceService:
    def __init__(self, config_id, project_name, user_identifier, team_name=None, comments=None):
        """Instantiates a new instance.

        Args:
            config_id: The ID of the DCA Create JSON config to use.
            project_name: The name of the Synapse project to create.
            user_identifier: The identifier (id, email, etc.) of the user creating the space.
            team_name: Name of the Synapse team to create and share on the project.
            comments: Open comments field.
        """

        self.start_time = datetime.now()
        self.config_id = config_id
        self.config = None
        self.project_name = project_name
        self.team_name = team_name
        self.user_identifier = user_identifier
        self.comments = comments
        self.project = None
        self.team = None
        self.errors = []
        self.warnings = []

    def execute(self):
        """Creates a new blank Synapse space.

        This method does not do validation. It expects all validation to have been done and passed already.

        Returns:
            Self
        """
        self.config = Env.SYNAPSE_SPACE_BASIC_CREATE_CONFIG_by_id(self.config_id)
        if self.config is None:
            raise Exception('Basic Create Space config not found for ID: {0}'.format(self.config_id))

        self.project = None
        self.team = None
        self.errors = []
        self.warnings = []

        if not self._create_project():
            self._write_synapse_log_file()
            return self

        self._set_storage_location()

        if self._create_team():
            self._assign_team_to_project()

        self._write_synapse_log_file()

        return self

    def _add_warning(self, msg):
        logger.warning(msg)
        self.warnings.append(msg)

    def _write_synapse_log_file(self):
        errors = []
        try:
            folder_id = Env.SYNAPSE_SPACE_LOG_FOLDER_ID()

            if folder_id:
                tmp_dir = tempfile.mkdtemp()

                try:
                    data = {
                        'parameters': {
                            'user': self.user_identifier,
                            'project_name': self.project_name,
                            'team_name': self.team_name,
                            'comments': self.comments,
                            'storage_location_id': Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID(),
                            'log_folder_id': Env.SYNAPSE_SPACE_LOG_FOLDER_ID(),
                            'basic_config': self.config
                        },
                        'project': {
                            'id': self.project.id if self.project else None,
                            'name': self.project.name if self.project else None
                        },
                        'team': {
                            'id': self.team.id if self.team else None,
                            'name': self.team.name if self.team else None
                        },
                        'warnings': self.warnings,
                        'errors': self.errors
                    }

                    logger.info('CREATE_SPACE_RESULT: {0}'.format(data))

                    file_name = '{0}_basic_create_space.json'.format(self.start_time.strftime('%Y%m%d_%H%M%S_%f'))
                    file_path = os.path.join(tmp_dir, file_name)

                    with open(file_path, 'w') as file:
                        file.write(json.dumps(data))

                    Synapse.client().store(syn.File(file_path, parent=folder_id))
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            else:
                self._add_warning(
                    'Environment Variable: SYNAPSE_SPACE_LOG_FOLDER_ID not set. Log files will not be created.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating log file: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _create_project(self):
        errors = []
        error = self.Validations.validate_project_name(self.project_name)
        if error:
            errors.append(error)
        else:
            try:
                logger.info('Creating project with name: {0}'.format(self.project_name))
                self.project = Synapse.client().store(syn.Project(name=self.project_name))
                logger.info('Project: {0} created with name: {1}'.format(self.project.id, self.project_name))
            except Exception as ex:
                logger.exception(ex)
                errors.append('Error creating project: {0}'.format(ex))

        self.errors += errors
        return self.project and not errors

    def _set_storage_location(self):
        errors = []
        try:
            storage_location_id = Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()

            if storage_location_id:
                logger.info(
                    'Setting storage location on project: {0} to: {1}'.format(self.project.id, storage_location_id))
                Synapse.client().setStorageLocation(self.project, storage_location_id)
                logger.info('Storage location set on project: {0}'.format(self.project.id))
            else:
                self._add_warning(
                    'Environment Variable: SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID not set. Cannot set storage location.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error setting storage location: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _create_team(self):
        errors = []
        if self.team_name:
            try:
                logger.info('Creating team with name: {0}'.format(self.team_name))
                self.team = Synapse.client().store(syn.Team(name=self.team_name))
                logger.info('Team created with name: {0}'.format(self.team_name))
            except Exception as ex:
                logger.exception(ex)
                errors.append('Error creating team: {0}'.format(ex))

        self.errors += errors
        return self.team and not errors

    def _assign_team_to_project(self):
        errors = []
        try:
            logger.info('Assigning team: {0} to project: {1}'.format(self.team.id, self.project.id))
            Synapse.client().setPermissions(self.project, self.team.id, accessType=Synapse.CAN_DOWNLOAD_PERMS)
            logger.info('Team: {0} assigned to project: {1}'.format(self.team.id, self.project.id))
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error assigning team to project: {0}'.format(ex))

        self.errors += errors
        return not errors

    class Validations:
        @classmethod
        def validate_project_name(cls, project_name):
            """Validates that a project name is available.

            Args:
                project_name: The project name to check.

            Returns:
                An error string or None.
            """

            error = None
            try:
                syn_project_id = Synapse.client().findEntityId(project_name)
                if syn_project_id:
                    project = Synapse.client().get(syn.Project(id=syn_project_id))
                    if project:
                        error = 'Project with name: "{0}" already exists.'.format(project_name)
            except Exception as ex:
                logger.exception(ex)
                error = 'Error validating project name: {0}'.format(ex)

            return error

        @classmethod
        def validate_team_name(cls, team_name):
            """Validates that a team name is available.

            Args:
                team_name: The team name to check.

            Returns:
                An error string or None.
            """
            error = None
            try:
                team = Synapse.client().getTeam(team_name)
                if team:
                    error = 'Team with name: "{0}" already exists.'.format(team_name)
            except ValueError:
                # Can't find team error
                pass
            except Exception as ex:
                logger.exception(ex)
                error = 'Error validating team name: {0}'.format(ex)

            return error
