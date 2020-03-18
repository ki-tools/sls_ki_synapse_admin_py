import os
import json
import shutil
import tempfile
from datetime import datetime
from www.core import Env
from www.core.log import logger
from www.core.synapse import Synapse
import synapseclient as syn


class CreateSpaceService:
    def __init__(self, project_name, institution_name, institution_short_name, user_identifier,
                 agreement_url=None, emails=None, start_date=None, end_date=None, comments=None):
        """Instantiates a new instance.

        Args:
            project_name: The name of the Synapse project to create.
            institution_name: The name of the institution the space is for.
            institution_short_name: The short name/code for the institution.
            user_identifier: The identifier (id, email, etc.) of the user creating the space.
            agreement_url: The URL of the data contribution agreement.
            emails: The emails to invite to the team that is created for the project.
            start_date: The start date of the agreement.
            end_date: The end date of the agreement.
            comments: Open comments field.
        """

        self.start_time = datetime.now()
        self.user_identifier = user_identifier
        self.project_name = project_name
        self.institution_name = institution_name
        self.institution_short_name = institution_short_name
        self.agreement_url = agreement_url
        self.emails = emails
        self.start_date = start_date
        self.end_date = end_date
        self.comments = comments
        self.project = None
        self.team = None
        self.errors = []
        self.warnings = []
        self.log_data = {}

    def execute(self):
        """Creates a new Synapse space for data contribution.

        This method does not do validation. It expects all validation to have been done and passed already.

        Returns:
            Self
        """

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
            self._add_team_managers()
            self._invite_emails_to_team()
            self._grant_team_access_to_entities()

        self._grant_principals_access_to_project()

        self._create_folders()

        self._create_wiki()

        self._update_tracking_tables()

        self._write_synapse_log_file()

        return self

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
                            'institution_name': self.institution_name,
                            'institution_short_name': self.institution_short_name,
                            'agreement_url': self.agreement_url,
                            'emails': self.emails,
                            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
                            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
                            'comments': self.comments,
                            'storage_location_id': Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID(),
                            'grant_team_access': Env.SYNAPSE_SPACE_DCA_CREATE_GRANT_TEAM_ENTITY_ACCESS(),
                            'grant_project_access': Env.SYNAPSE_SPACE_DCA_CREATE_GRANT_PROJECT_ACCESS(),
                            'folder_names': Env.SYNAPSE_SPACE_DCA_CREATE_FOLDER_NAMES(),
                            'wiki_project_id': Env.SYNAPSE_SPACE_DCA_CREATE_WIKI_PROJECT_ID(),
                            'contribution_agreement_table_id': Env.SYNAPSE_SPACE_DCA_CREATE_CONTRIBUTION_AGREEMENT_TABLE_ID(),
                            'log_folder_id': Env.SYNAPSE_SPACE_LOG_FOLDER_ID()
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

                    file_name = '{0}_dca_create_space.json'.format(self.start_time.strftime('%Y%m%d_%H%M%S_%f'))
                    file_path = os.path.join(tmp_dir, file_name)

                    with open(file_path, 'w') as file:
                        file.write(json.dumps(data))

                    Synapse.client().store(syn.File(file_path, parent=folder_id))
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            else:
                self.warnings.append(
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
                self.warnings.append(
                    'Environment Variable: SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID not set. Cannot set storage location.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error setting storage location: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _create_team(self):
        errors = []
        team_name = 'KiContributor_{0}'.format(self.project.name)
        try:
            logger.info('Creating team with name: {0}'.format(team_name))
            self.team = Synapse.client().store(syn.Team(name=team_name))
            logger.info('Team created with name: {0}'.format(team_name))
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating team: {0}'.format(ex))

        self.errors += errors
        return self.team and not errors

    def _assign_team_to_project(self):
        errors = []
        try:
            logger.info('Assigning team: {0} to project: {1}'.format(self.team.id, self.project.id))
            Synapse.client().setPermissions(self.project, self.team.id, accessType=Synapse.CAN_EDIT_AND_DELETE_PERMS)
            logger.info('Team: {0} assigned to project: {1}'.format(self.team.id, self.project.id))
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error assigning team to project: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _add_team_managers(self):
        errors = []
        try:
            user_ids = Env.SYNAPSE_SPACE_DCA_CREATE_TEAM_MANAGER_USER_IDS()

            if user_ids:
                for user_id in user_ids:
                    logger.info('Inviting user: {0} to team: {1}.'.format(user_id, self.team.id))
                    body = {
                        'teamId': self.team.id,
                        'inviteeId': user_id
                    }
                    Synapse.client().restPOST('/membershipInvitation', body=json.dumps(body))
                    logger.info('User: {0} invited to team: {1}'.format(user_id, self.team.id))

                    logger.info('Setting user: {0} as manager on team: {1}.'.format(user_id, self.team.id))
                    new_acl = {'principalId': user_id, 'accessType': Synapse.TEAM_MANAGER_PERMS}
                    acl = Synapse.client().restGET('/team/{0}/acl'.format(self.team.id))
                    acl['resourceAccess'].append(new_acl)
                    Synapse.client().restPUT("/team/acl", body=json.dumps(acl))
                    logger.info('User: {0} has been given manager access on team: {1}.'.format(user_id, self.team.id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DCA_CREATE_TEAM_MANAGER_USER_IDS not set. Team managers will not be added to the project team.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error adding managers to the project team: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _invite_emails_to_team(self):
        errors = []
        if self.emails:
            try:
                for email in self.emails:
                    logger.info('Inviting email: {0} to team: {1}'.format(email, self.team.id))
                    body = {
                        'teamId': self.team.id,
                        'inviteeEmail': email
                    }
                    Synapse.client().restPOST('/membershipInvitation', body=json.dumps(body))
                    logger.info('Email: {0} invited to team: {1}'.format(email, self.team.id))
            except Exception as ex:
                logger.exception(ex)
                errors.append('Error inviting emails to team: {0}'.format(ex))
        else:
            self.warnings.append('No emails specified. No users will be invited to this project.')

        self.errors += errors
        return not errors

    def _grant_team_access_to_entities(self):
        errors = []
        try:
            config = Env.SYNAPSE_SPACE_DCA_CREATE_GRANT_TEAM_ENTITY_ACCESS()

            if config:
                for item in config:
                    entity_id = item['id']
                    permission_code = item['permission']
                    access_type = Synapse.get_perms_by_code(permission_code)

                    logger.info('Granting team: {0} permission: {1} to entity: {2}'.format(self.team.name,
                                                                                           permission_code,
                                                                                           entity_id))

                    Synapse.client().setPermissions(entity_id, principalId=self.team.id, accessType=access_type)
                    logger.info('Team: {0} granted access to entity: {1}'.format(self.team.name, entity_id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DCA_CREATE_GRANT_TEAM_ENTITY_ACCESS not set. Project team will not be shared on other entities.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error sharing project team with entities: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _grant_principals_access_to_project(self):
        errors = []
        try:
            config = Env.SYNAPSE_SPACE_DCA_CREATE_GRANT_PROJECT_ACCESS()

            if config:
                for item in config:
                    principal_id = item['id']
                    permission_code = item['permission']
                    access_type = Synapse.get_perms_by_code(permission_code)

                    logger.info('Assigning principal: {0} to project: {1} with permission: {2}'.format(principal_id,
                                                                                                       self.project.id,
                                                                                                       permission_code))

                    Synapse.client().setPermissions(self.project, principalId=principal_id, accessType=access_type)
                    logger.info('Principal: {0} assigned to project: {1}'.format(principal_id, self.project.id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DCA_CREATE_GRANT_PROJECT_ACCESS not set. Principals will not be added to this project.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error adding principals to project: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _create_folders(self):
        errors = []
        try:
            folder_names = Env.SYNAPSE_SPACE_DCA_CREATE_FOLDER_NAMES()

            if folder_names:
                for folder_path in folder_names:
                    folder_path_parts = list(filter(None, folder_path.split('/')))
                    parent = self.project

                    for folder_name in folder_path_parts:
                        logger.info('Creating folder: {0} in project: {1}'.format(folder_name, self.project.id))
                        parent = Synapse.client().store(syn.Folder(name=folder_name, parent=parent))
                        logger.info('Folder: {0} created in project: {1}'.format(folder_name, self.project.id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DCA_CREATE_FOLDER_NAMES not set. Folders will not be created in this project.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating folders: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _create_wiki(self):
        errors = []
        try:
            source_wiki_project_id = Env.SYNAPSE_SPACE_DCA_CREATE_WIKI_PROJECT_ID()

            if source_wiki_project_id:
                source_wiki = Synapse.client().getWiki(source_wiki_project_id)

                # TODO: Do we need to handle attachments on the wiki?
                new_wiki = syn.Wiki(
                    owner=self.project,
                    title=source_wiki.get('title'),
                    markdown=source_wiki.get('markdown')
                )
                logger.info('Importing wiki from project: {0} into project: {1}'.format(source_wiki_project_id,
                                                                                        self.project.id))
                Synapse.client().store(new_wiki)
                logger.info('Wiki imported from project: {0} into project: {1}'.format(source_wiki_project_id,
                                                                                       self.project.id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DCA_CREATE_WIKI_PROJECT_ID not set. Wiki will not be created in this project.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating wiki: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _update_tracking_tables(self):
        result = False

        if not self._update_contribution_agreement_table():
            result = False

        if not self._update_contributor_tracking_scope():
            result = False

        return result

    def _update_contribution_agreement_table(self):
        errors = []
        try:
            table_id = Env.SYNAPSE_SPACE_DCA_CREATE_CONTRIBUTION_AGREEMENT_TABLE_ID()

            if table_id:
                row = Synapse.build_syn_table_row(table_id, {
                    'Organization': self.institution_name,
                    'Contact': self.emails[0] if self.emails else None,
                    'Synapse_Project_ID': self.project.id,
                    'Synapse_Team_ID': self.team.id if self.team else None,
                    'Agreement_Link': self.agreement_url,
                    'Start_Date': Synapse.date_to_synapse_date_timestamp(self.start_date),
                    'End_Date': Synapse.date_to_synapse_date_timestamp(self.end_date),
                    'Comments': self.comments
                })

                logger.info(
                    'Updating contribution agreement table: {0} for project: {1}'.format(table_id, self.project.id))
                Synapse.client().store(syn.Table(table_id, [row]))
                logger.info(
                    'Contribution agreement table: {0} updated for project: {1}'.format(table_id, self.project.id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DCA_CREATE_CONTRIBUTION_AGREEMENT_TABLE_ID not set. Contribution agreement table will not be updated.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error updating contribution agreement table: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _update_contributor_tracking_scope(self):
        """Add the project to the KiData_Contributor_Tracking table's scope so the files in the project are included.
        """
        errors = []
        try:
            view_id = Env.SYNAPSE_SPACE_DCA_CREATE_CONTRIBUTOR_TRACKING_VIEW_ID()

            if view_id:
                view = Synapse.client().get(view_id)
                view.properties.scopeIds.append(self.project.id)

                logger.info('Updating contributor tracking view: {0} for project: {1}'.format(view_id, self.project.id))
                Synapse.client().store(view)
                logger.info('Contributor tracking view: {0} updated for project: {1}'.format(view_id, self.project.id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DCA_CREATE_CONTRIBUTOR_TRACKING_VIEW_ID not set. Contributor tracking view will not be updated.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error updating contributor tracking view: {0}'.format(ex))

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
