from www.core import Env
from www.core.log import logger
from www.core.synapse import Synapse
import synapseclient as syn
import json


class CreateSynapseSpaceService:
    DEFAULT_FOLDER_NAMES = ['Research Data', 'Metadata', 'Supporting Documentation']

    def __init__(self, project_name, institution_name, emails=None):
        self.project_name = project_name
        self.institution_name = institution_name
        self.emails = emails
        self.project = None
        self.team = None
        self.errors = []
        self.warnings = []

    def execute(self):
        self.project = None
        self.errors = []
        self.warnings = []

        # Create the Project
        if not self._create_project():
            return self

        # Set the storage location
        if not self._set_storage_location():
            return self

        # Create the Team
        if not self._create_team():
            return self

        # Add the Team to the Project with Edit/Delete permissions.
        if not self._assign_team_to_project():
            return self

        # Invite all the emails to the team.
        if not self._invite_emails_to_team():
            return self

        # Add the admin teams to the Project with Edit/Delete permissions.
        if not self._assign_admin_teams_to_project():
            return self

        # Create Folders
        if not self._create_folders():
            return self

        # Set the Wiki
        if not self._create_wiki():
            return self

        # Update tracking table(s)
        # TODO: implement this...

        return self

    def _create_project(self):
        error = self.Validations.validate_project_name(self.project_name)
        if error:
            self.errors.append(error)
        elif not self.project:
            try:
                self.project = Synapse.client().store(syn.Project(name=self.project_name))
            except Exception as ex:
                logger.exception(ex)
                self.errors.append('Error creating project: {0}'.format(ex))

        return self.project and not self.errors

    def _set_storage_location(self):
        try:
            storage_location_id = Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()

            if storage_location_id:
                Synapse.client().setStorageLocation(self.project, storage_location_id)
            else:
                self.warnings.append(
                    'Environment variable: SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID not set. Cannot set storage location.')
        except Exception as ex:
            logger.exception(ex)
            self.errors.append('Error setting storage location: {0}'.format(ex))

        return not self.errors

    def _create_team(self):
        team_name = self.project.name
        try:
            self.team = Synapse.client().store(syn.Team(name=team_name))
        except Exception as ex:
            logger.exception(ex)
            self.errors.append('Error creating team: {0}'.format(ex))

        return self.team and not self.errors

    def _assign_team_to_project(self):
        try:
            Synapse.client().setPermissions(self.project, self.team.id, accessType=Synapse.CAN_EDIT_AND_DELETE_PERMS)
        except Exception as ex:
            logger.exception(ex)
            self.errors.append('Error assigning team to project: {0}'.format(ex))

        return not self.errors

    def _invite_emails_to_team(self):
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
                self.errors.append('Error inviting emails to team: {0}'.format(ex))
        else:
            self.warnings.append('No emails specified. No users will be invited to this project.')

        return not self.errors

    def _assign_admin_teams_to_project(self):
        try:
            team_ids = Env.CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS()

            if team_ids:
                for team_id in team_ids:
                    Synapse.client().setPermissions(self.project,
                                                    principalId=team_id,
                                                    accessType=Synapse.CAN_EDIT_AND_DELETE_PERMS)
            else:
                self.warnings.append(
                    'Environment variable: CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS not set. Admin teams will not be added to this project.')
        except Exception as ex:
            logger.exception(ex)
            self.errors.append('Error adding admin teams to project: {0}'.format(ex))

        return not self.errors

    def _create_folders(self):
        try:
            for folder_name in self.DEFAULT_FOLDER_NAMES:
                Synapse.client().store(syn.Folder(name=folder_name, parent=self.project))
        except Exception as ex:
            logger.exception(ex)
            self.errors.append('Error creating folders: {0}'.format(ex))

        return not self.errors

    def _create_wiki(self):
        try:
            source_wiki_project_id = Env.CREATE_SYNAPSE_SPACE_DEFAULT_WIKI_PROJECT_ID()

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
                    'Environment variable: CREATE_SYNAPSE_SPACE_DEFAULT_WIKI_PROJECT_ID not set. Wiki will not be created in this project.')
        except Exception as ex:
            logger.exception(ex)
            self.errors.append('Error creating wiki: {0}'.format(ex))

        return not self.errors

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
