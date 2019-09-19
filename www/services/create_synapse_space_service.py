from www.core import Env
from www.core.log import logger
from www.core.synapse import Synapse
import synapseclient as syn
import json


class CreateSynapseSpaceService:
    def __init__(self, project_name, institution_name, agreement_url=None, emails=None):
        self.project_name = project_name
        self.institution_name = institution_name
        self.agreement_url = agreement_url
        self.emails = emails
        self.project = None
        self.team = None
        self.errors = []
        self.warnings = []

    def execute(self):
        self.project = None
        self.team = None
        self.errors = []
        self.warnings = []

        if not self._create_project():
            return self

        self._set_storage_location()

        if self._create_team():
            self._assign_team_to_project()
            self._invite_emails_to_team()

        self._assign_admin_teams_to_project()

        self._create_folders()

        self._create_wiki()

        self._update_tracking_tables()

        return self

    def _create_project(self):
        errors = []
        error = self.Validations.validate_project_name(self.project_name)
        if error:
            errors.append(error)
        else:
            try:
                self.project = Synapse.client().store(syn.Project(name=self.project_name))
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
                Synapse.client().setStorageLocation(self.project, storage_location_id)
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
        team_name = self.project.name
        try:
            self.team = Synapse.client().store(syn.Team(name=team_name))
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating team: {0}'.format(ex))

        self.errors += errors
        return self.team and not errors

    def _assign_team_to_project(self):
        errors = []
        try:
            Synapse.client().setPermissions(self.project, self.team.id, accessType=Synapse.CAN_EDIT_AND_DELETE_PERMS)
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error assigning team to project: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _invite_emails_to_team(self):
        errors = []
        if self.emails:
            try:
                for email in self.emails:
                    body = {
                        'teamId': self.team.id,
                        'inviteeEmail': email
                    }
                    Synapse.client().restPOST('/membershipInvitation', body=json.dumps(body))
            except Exception as ex:
                logger.exception(ex)
                errors.append('Error inviting emails to team: {0}'.format(ex))
        else:
            self.warnings.append('No emails specified. No users will be invited to this project.')

        self.errors += errors
        return not errors

    def _assign_admin_teams_to_project(self):
        errors = []
        try:
            team_ids = Env.CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS()

            if team_ids:
                for team_id in team_ids:
                    Synapse.client().setPermissions(self.project,
                                                    principalId=team_id,
                                                    accessType=Synapse.CAN_EDIT_AND_DELETE_PERMS)
            else:
                self.warnings.append(
                    'Environment Variable: CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS not set. Admin teams will not be added to this project.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error adding admin teams to project: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _create_folders(self):
        errors = []
        try:
            folder_names = Env.CREATE_SYNAPSE_SPACE_FOLDER_NAMES()

            if folder_names:
                for folder_name in folder_names:
                    Synapse.client().store(syn.Folder(name=folder_name, parent=self.project))
            else:
                self.warnings.append(
                    'Environment Variable: CREATE_SYNAPSE_SPACE_FOLDER_NAMES not set. Folders will not be created in this project.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating folders: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _create_wiki(self):
        errors = []
        try:
            source_wiki_project_id = Env.CREATE_SYNAPSE_SPACE_WIKI_PROJECT_ID()

            if source_wiki_project_id:
                source_wiki = Synapse.client().getWiki(source_wiki_project_id)

                # TODO: Do we need to handle attachments on the wiki?
                new_wiki = syn.Wiki(
                    owner=self.project,
                    title=source_wiki.get('title'),
                    markdown=source_wiki.get('markdown')
                )
                Synapse.client().store(new_wiki)
            else:
                self.warnings.append(
                    'Environment Variable: CREATE_SYNAPSE_SPACE_WIKI_PROJECT_ID not set. Wiki will not be created in this project.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating wiki: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _update_tracking_tables(self):
        result = False

        if not self._update_contribution_agreement_table():
            result = False

        return result

    def _update_contribution_agreement_table(self):
        errors = []
        try:
            table_id = Env.CREATE_SYNAPSE_SPACE_CONTRIBUTION_AGREEMENT_TABLE_ID()

            if table_id:
                row = self._build_syn_table_row(table_id, {
                    'Organization': self.institution_name,
                    'Contact': self.emails[0] if self.emails else None,
                    'Synapse_Project_ID': self.project.id,
                    'Synapse_Team_ID': self.team.id if self.team else None,
                    'Agreement_Link': self.agreement_url
                })

                Synapse.client().store(syn.Table(table_id, [row]))
            else:
                self.warnings.append(
                    'Environment Variable: CREATE_SYNAPSE_SPACE_CONTRIBUTION_AGREEMENT_TABLE_ID not set. Contribution agreement table will not be updated.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error updating contribution agreement table: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _build_syn_table_row(self, syn_table_id, row_data):
        """Builds an array of row values for a Synapse Table.

        Args:
            syn_table_id: The ID of the Synapse table to add a row to.
            row_data: Dictionary of field names and values.

        Returns:
            Array
        """
        table_columns = [c['name'] for c in list(Synapse.client().getTableColumns(syn_table_id))]

        # Make sure the specified fields exist in the table.
        for column in row_data:
            if column not in table_columns:
                raise Exception('Column: {0} does not exist in table: {1}'.format(column, syn_table_id))

        # Build the row data.
        new_row = []

        for column in table_columns:
            if column in row_data:
                new_row.append(row_data[column])
            else:
                new_row.append(None)

        return new_row

    class Validations:
        @classmethod
        def validate_project_name(cls, project_name):
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
