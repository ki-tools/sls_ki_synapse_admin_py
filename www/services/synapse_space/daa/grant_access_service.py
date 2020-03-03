import os
import json
import shutil
import tempfile
from datetime import datetime
from www.core import Env
from www.core.log import logger
from www.core.synapse import Synapse
import synapseclient as syn


class GrantAccessService:
    def __init__(self, team_name, institution_name, institution_short_name, data_collection_name, user_identifier,
                 agreement_url=None, emails=None, start_date=None, end_date=None, comments=None):
        """Instantiates a new instance.

        Args:
            team_name: The name of the Synapse project to create.
            institution_name: The name of the institution the space is for.
            institution_short_name: The short name/code for the institution.
            data_collection_name: The data collection to grant access to.
            user_identifier: The identifier (id, email, etc.) of the user creating the space.
            agreement_url: The URL of the data access agreement.
            emails: The emails to invite to the team that is created for the project.
            start_date: The start date of the agreement.
            end_date: The end date of the agreement.
            comments: Open comments field.
        """

        self.start_time = datetime.now()
        self.team_name = team_name
        self.institution_name = institution_name
        self.institution_short_name = institution_short_name
        self.data_collection_name = data_collection_name
        self.user_identifier = user_identifier
        self.agreement_url = agreement_url
        self.emails = emails
        self.start_date = start_date
        self.end_date = end_date
        self.comments = comments
        self.team = None
        self.data_collection = None
        self.errors = []
        self.warnings = []
        self.log_data = {}

    def execute(self):
        """Creates a new Synapse team for data access.

        This method does not do validation. It expects all validation to have been done and passed already.

        Returns:
            Self
        """

        self.team = None
        self.errors = []
        self.warnings = []

        if self._create_team():
            self._grant_team_access()
            self._add_team_managers()
            self._invite_emails_to_team()

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
                            'team_name': self.team_name,
                            'institution_name': self.institution_name,
                            'institution_short_name': self.institution_short_name,
                            'data_collection_name': self.data_collection_name,
                            'agreement_url': self.agreement_url,
                            'emails': self.emails,
                            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
                            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
                            'comments': self.comments,
                            'access_agreement_table_id': Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_AGREEMENT_TABLE_ID(),
                            'log_folder_id': Env.SYNAPSE_SPACE_LOG_FOLDER_ID()
                        },
                        'team': {
                            'id': self.team.id if self.team else None,
                            'name': self.team.name if self.team else None
                        },
                        'data_collection': self.data_collection,
                        'warnings': self.warnings,
                        'errors': self.errors
                    }

                    logger.info('SYNAPSE_SPACE_DAA_GRANT_SYNAPSE_ACCESS_RESULT: {0}'.format(data))

                    file_name = '{0}_daa_grant_access.json'.format(self.start_time.strftime('%Y%m%d_%H%M%S_%f'))
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

    def _create_team(self):
        errors = []
        try:
            logger.info('Creating team with name: {0}'.format(self.team_name))
            self.team = Synapse.client().store(syn.Team(name=self.team_name))
            logger.info('Team created with name: {0}'.format(self.team_name))
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error creating team: {0}'.format(ex))

        self.errors += errors
        return self.team and not errors

    def _grant_team_access(self):
        errors = []
        try:
            config = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_DATA_COLLECTIONS()

            if config:
                self.data_collection = next((c for c in config if c['name'] == self.data_collection_name), None)
                name = self.data_collection['name']
                ids = [c['id'] for c in self.data_collection['entities']]
                access_type = Synapse.CAN_DOWNLOAD_PERMS

                for syn_id in ids:
                    logger.info(
                        'Granting team: {0} CAN DOWNLOAD permission to entity: {1} for data collection: {2}'.format(
                            self.team.name, syn_id, name))
                    Synapse.client().setPermissions(syn_id, principalId=self.team.id, accessType=access_type)
                    logger.info('Team: {0} granted access to entity: {1}'.format(self.team.name, syn_id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DAA_GRANT_ACCESS_DATA_COLLECTIONS not set. Data collection will not be shared with team.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error sharing data collection with team: {0}'.format(ex))

        self.errors += errors
        return not errors

    def _add_team_managers(self):
        errors = []
        try:
            user_ids = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_TEAM_MANAGER_USER_IDS()

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
                    'Environment Variable: SYNAPSE_SPACE_DAA_GRANT_ACCESS_TEAM_MANAGER_USER_IDS not set. Team managers will not be added to the project team.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error adding managers to the team: {0}'.format(ex))

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
            self.warnings.append('No emails specified. No users will be invited to the team.')

        self.errors += errors
        return not errors

    def _update_tracking_tables(self):
        result = False

        if not self._update_access_agreement_table():
            result = False

        return result

    def _update_access_agreement_table(self):
        errors = []
        try:
            table_id = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_AGREEMENT_TABLE_ID()

            if table_id:
                row = Synapse.build_syn_table_row(table_id, {
                    'Organization': self.institution_name,
                    'Contact': self.emails[0] if self.emails else None,
                    'Synapse_Team_ID': self.team.id if self.team else None,
                    'Granted_Entity_IDs': ', '.join('{0} ({1})'.format(c['id'], c['name']) for c in
                                                    self.data_collection['entities']) if self.data_collection else None,
                    'Agreement_Link': self.agreement_url,
                    'Start_Date': Synapse.date_to_synapse_date_timestamp(self.start_date),
                    'End_Date': Synapse.date_to_synapse_date_timestamp(self.end_date),
                    'Comments': self.comments
                })

                logger.info('Updating access agreement table: {0} for team: {1}'.format(table_id, self.team.id))
                Synapse.client().store(syn.Table(table_id, [row]))
                logger.info('Access agreement table: {0} updated for team: {1}'.format(table_id, self.team.id))
            else:
                self.warnings.append(
                    'Environment Variable: SYNAPSE_SPACE_DAA_GRANT_ACCESS_AGREEMENT_TABLE_ID not set. Access agreement table will not be updated.')
        except Exception as ex:
            logger.exception(ex)
            errors.append('Error updating access agreement table: {0}'.format(ex))

        self.errors += errors
        return not errors

    class Validations:
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
